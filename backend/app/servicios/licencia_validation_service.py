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


def _name_tokens(value: str | None) -> set[str]:
    normalized = _normalize(value)
    if not normalized:
        return set()
    return set(re.findall(r"[a-z0-9]+", normalized))


def _matches_person_field(extracted_value: str | None, expected_value: str | None) -> bool:
    extracted_norm = _normalize(extracted_value)
    expected_norm = _normalize(expected_value)

    if not extracted_norm or not expected_norm:
        return False

    if extracted_norm == expected_norm:
        return True

    extracted_tokens = _name_tokens(extracted_norm)
    expected_tokens = _name_tokens(expected_norm)
    if not extracted_tokens or not expected_tokens:
        return False

    # Acepta nombres compuestos cuando uno contiene todos los tokens del otro.
    return extracted_tokens.issubset(expected_tokens) or expected_tokens.issubset(extracted_tokens)


def _prefer_complete_expected_field(extracted_value: str | None, expected_value: str | None) -> str | None:
    """Si el OCR trae un campo parcial, prioriza el valor completo esperado."""
    if not _matches_person_field(extracted_value, expected_value):
        return extracted_value

    extracted_tokens = _name_tokens(extracted_value)
    expected_tokens = _name_tokens(expected_value)

    if not expected_tokens:
        return extracted_value

    if extracted_tokens and extracted_tokens.issubset(expected_tokens) and extracted_tokens != expected_tokens:
        return expected_value

    return extracted_value


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

        # Evita devolver nombres truncados cuando el OCR reconoce solo una parte.
        extracted["nombre"] = _prefer_complete_expected_field(extracted.get("nombre"), nombre)
        extracted["apellido"] = _prefer_complete_expected_field(extracted.get("apellido"), apellido)

        coincidencias = {
            "nombre": _matches_person_field(extracted.get("nombre"), nombre),
            "apellido": _matches_person_field(extracted.get("apellido"), apellido),
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
