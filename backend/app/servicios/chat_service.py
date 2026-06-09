from datetime import datetime, timezone
import re

from app.adaptadores.groq_adapter import GroqChatAdapter
from app.servicios.bot_service import BotService

_bot_service = BotService()
_groq = GroqChatAdapter()


class BotExternalServiceError(RuntimeError):
    pass


_SOLICITUD_PERSONA_PATTERNS = [
    r"\b(persona|humano|operador|asesor|agente|representante|soporte)\b",
    r"hablar con (una )?(persona|humano|operador|asesor|agente|representante)",
    r"me deriv[ée]s? con (una )?(persona|humano|operador|asesor|agente|representante|soporte)",
]

_RESPUESTA_SIN_RESOLVER_PATTERNS = [
    "no puedo ayudarte",
    "no tengo información",
    "no dispongo de información",
    "no estoy seguro",
    "no puedo determinar",
    "contacta a soporte",
    "contactar a soporte",
    "deriv",
]


def requiere_soporte_por_pregunta(pregunta: str) -> bool:
    pregunta_normalizada = pregunta.lower().strip()
    return any(re.search(pattern, pregunta_normalizada, re.IGNORECASE) for pattern in _SOLICITUD_PERSONA_PATTERNS)


def requiere_soporte_por_respuesta(respuesta: str) -> bool:
    respuesta_normalizada = respuesta.lower().strip()
    return any(patron in respuesta_normalizada for patron in _RESPUESTA_SIN_RESOLVER_PATTERNS)


def mensaje_derivacion(motivo: str) -> str:
    if motivo == "solicitud_usuario":
        return "Te derivo con una persona de soporte para que continúe la conversación."
    return "No pude resolver tu consulta automáticamente. Te derivo con una persona de soporte."


def ask_bot(pregunta: str, prompt_key: str) -> dict:
    system_prompt = _bot_service.get_system_prompt(prompt_key)
    try:
        cuerpo = _groq.chat(system_prompt, pregunta)
    except Exception as error:
        raise BotExternalServiceError("No se pudo conectar con el servicio del chatbot") from error

    return {
        "cuerpo": cuerpo,
        "autor": "bot",
        "enviado_at": datetime.now(timezone.utc).isoformat(),
    }
