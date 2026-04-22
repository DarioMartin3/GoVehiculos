import base64
import re
import unicodedata
from datetime import date

from app.adaptadores.document_validator import DocumentValidatorAdapter
from app.prompts.licencia_prompt import PROMPT_LICENCIA


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    v = value.strip().lower()
    return unicodedata.normalize("NFD", v).encode("ascii", "ignore").decode("ascii")


def _normalize_date(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip()
    match = re.match(r"(\d{2})/(\d{2})/(\d{4})", value)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    return value


class LicenciaValidationService:
    def __init__(self, adapter: DocumentValidatorAdapter):
        self.adapter = adapter

    def validate(
        self,
        image_bytes: bytes,
        nombre: str,
        apellido: str,
        fecha_nacimiento: str,
    ) -> dict:
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        extracted = self.adapter.extraer_datos(PROMPT_LICENCIA, image_b64)

        coincidencias = {
            "nombre": _normalize(extracted.get("nombre")) == _normalize(nombre),
            "apellido": _normalize(extracted.get("apellido")) == _normalize(apellido),
            "fecha_nacimiento": _normalize_date(extracted.get("fecha_nacimiento")) == _normalize_date(fecha_nacimiento),
        }

        fecha_venc_raw = _normalize_date(extracted.get("fecha_vencimiento") or "")
        vencida = False
        if fecha_venc_raw:
            try:
                vencida = date.fromisoformat(fecha_venc_raw) < date.today()
            except ValueError:
                pass

        persona_valida = all(coincidencias.values())
        valido = persona_valida and not vencida

        return {
            "valido": valido,
            "persona_valida": persona_valida,
            "vencida": vencida,
            "coincidencias": coincidencias,
            "datos_extraidos": extracted,
            "mensaje": self._build_message(persona_valida, vencida, coincidencias),
        }

    def _build_message(self, persona_valida: bool, vencida: bool, coincidencias: dict) -> str:
        if vencida:
            return "La licencia está vencida."
        if not persona_valida:
            campos = ", ".join(k for k, v in coincidencias.items() if not v)
            return f"Los datos no coinciden con el titular: {campos}."
        return "Licencia validada correctamente."
