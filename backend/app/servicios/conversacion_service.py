from datetime import datetime, timezone

from app.core.database import get_connection
from app.entidades.mensaje import Mensaje
from app.repositorios.conversacion_repository import ConversacionRepository

_repo = ConversacionRepository()


def iniciar_conversacion(prompt_key: str, usuario_id: int | None = None) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            fase_id = _repo.get_fase_id(cursor, "bot_libre")
            tema_id = _repo.get_tema_id_by_prompt_key(cursor, prompt_key)
            conversacion_id = _repo.crear_conversacion(cursor, tema_id, fase_id, usuario_id)
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


def obtener_conversacion(conversacion_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            conversacion = _repo.get_conversacion_by_id(cursor, conversacion_id)

    if not conversacion:
        raise ValueError(f"Conversación '{conversacion_id}' no encontrada")

    return conversacion


def obtener_mensajes_conversacion(conversacion_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            mensajes = _repo.get_mensajes_by_conversacion_id(cursor, conversacion_id)

    return mensajes


def derivar_conversacion_a_soporte(conversacion_id: int, motivo: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            fase_id = _repo.get_fase_id(cursor, "operario")
            _repo.actualizar_fase_conversacion(cursor, conversacion_id, fase_id)
            operario_id = _repo.get_support_operator_id(cursor)
            derivacion_id = _repo.crear_derivacion(cursor, conversacion_id, operario_id, motivo)
        conn.commit()

    return {
        "conversacion_id": conversacion_id,
        "fase": "operario",
        "derivacion_id": derivacion_id,
        "operario_id": operario_id,
    }


def cerrar_conversacion(conversacion_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            fase_id = _repo.get_fase_id(cursor, "cerrada")
            updated = _repo.cerrar_conversacion(cursor, conversacion_id, fase_id)
        conn.commit()

    if not updated:
        raise ValueError(f"Conversación '{conversacion_id}' no encontrada o ya cerrada")
