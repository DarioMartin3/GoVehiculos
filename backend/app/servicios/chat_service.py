from datetime import datetime, timezone

from app.adaptadores.groq_adapter import GroqChatAdapter
from app.servicios.bot_service import BotService

_bot_service = BotService()
_groq = GroqChatAdapter()


def ask_bot(pregunta: str, prompt_key: str) -> dict:
    system_prompt = _bot_service.get_system_prompt(prompt_key)
    cuerpo = _groq.chat(system_prompt, pregunta)

    return {
        "cuerpo": cuerpo,
        "autor": "bot",
        "enviado_at": datetime.now(timezone.utc).isoformat(),
    }
