import json
import re
import base64
import requests

from app.core.config import GROQ_API_KEY


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().lower()


def _normalize_date(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip()
    match = re.match(r"(\d{2})/(\d{2})/(\d{4})", value)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    return value


def _normalize_dni(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[.\s-]", "", value.strip())


class DocumentValidationService:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY no configurada")

    def validate(
        self,
        image_bytes: bytes,
        nombre: str,
        apellido: str,
        dni: str,
        fecha_nacimiento: str,
    ) -> dict:
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        prompt = """Analizá esta imagen de un documento de identidad argentino (DNI).
Extraé los siguientes campos y devolvé ÚNICAMENTE un JSON válido con esta estructura, sin texto adicional:
{
  "nombre": "<nombre/s de pila>",
  "apellido": "<apellido/s>",
  "dni": "<número de DNI sin puntos ni espacios>",
  "fecha_nacimiento": "<fecha en formato YYYY-MM-DD>"
}
Si no podés leer algún campo con certeza, dejá el valor como cadena vacía."""

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "max_tokens": 256,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            },
        )

        if not response.ok:
            raise ValueError(f"Groq error {response.status_code}: {response.text}")

        raw = response.json()["choices"][0]["message"]["content"].strip()
        print("=== RESPUESTA GROQ ===")
        print(raw)
        print("=====================")

        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            raise ValueError("No se pudo interpretar la respuesta del modelo")

        extracted = json.loads(json_match.group())

        coincidencias = {
            "nombre": _normalize(extracted.get("nombre")) == _normalize(nombre),
            "apellido": _normalize(extracted.get("apellido")) == _normalize(apellido),
            "dni": _normalize_dni(extracted.get("dni")) == _normalize_dni(dni),
            "fecha_nacimiento": _normalize_date(extracted.get("fecha_nacimiento")) == _normalize_date(fecha_nacimiento),
        }

        valido = all(coincidencias.values())

        return {
            "valido": valido,
            "campos_detectados": extracted,
            "coincidencias": coincidencias,
            "mensaje": "Documento validado correctamente." if valido else f"No coinciden los campos: {', '.join(k for k, v in coincidencias.items() if not v)}.",
        }
