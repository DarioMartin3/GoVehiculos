from datetime import datetime, timezone

from app.core.database import get_connection
from app.entidades.mensaje import Mensaje
from app.repositorios.conversacion_repository import ConversacionRepository

_repo = ConversacionRepository()


def iniciar_conversacion(prompt_key: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            fase_id = _repo.get_fase_id(cursor, "bot_libre")
            tema_id = _repo.get_tema_id_by_prompt_key(cursor, prompt_key)
            conversacion_id = _repo.crear_conversacion(cursor, tema_id, fase_id)
        conn.commit()

    return {"conversacion_id": conversacion_id, "tema_id": tema_id, "fase": "bot_libre"}


def guardar_mensaje(conversacion_id: int, autor_id: int, mensaje: dict) -> Mensaje:
    enviado_at = datetime.fromisoformat(mensaje["enviado_at"]).astimezone(timezone.utc)

    entidad = Mensaje(
        conversacion_id=conversacion_id,
        autor_id=autor_id,
        autor=mensaje["autor"],
        cuerpo=mensaje["cuerpo"],
        enviado_at=enviado_at,
    )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            entidad.id = _repo.insertar_mensaje(cursor, entidad)
        conn.commit()

    return entidad
