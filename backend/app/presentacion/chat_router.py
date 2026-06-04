from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, status

from app.schemas import (
    ConversacionResponse,
    ConversacionMensajeResponse,
    EnviarMensajeRequest,
    IniciarConversacionRequest,
    IniciarConversacionResponse,
    MensajeResponse,
)
from app.servicios.auth_service import AuthService
from app.servicios.chat_service import (
    ask_bot,
    mensaje_derivacion,
    requiere_soporte_por_pregunta,
    requiere_soporte_por_respuesta,
)
from app.servicios.conversacion_service import (
    cerrar_conversacion,
    derivar_conversacion_a_soporte,
    guardar_mensaje,
    iniciar_conversacion,
    obtener_conversacion,
    obtener_mensajes_conversacion,
)
from app.core.database import get_connection
from fastapi import WebSocket, WebSocketDisconnect, Query
from app.presentacion.ws_manager import manager as ws_manager
from app.repositorios.conversacion_repository import ConversacionRepository

router = APIRouter(prefix="/chat", tags=["chat"])

_repo = ConversacionRepository()


def _get_auth_context(authorization: str | None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    token = authorization.split(" ", 1)[1].strip()
    try:
        result = AuthService().get_profile(token)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error
    return result


def _mensaje_response_from_dict(data: dict, **extra: object) -> MensajeResponse:
    return MensajeResponse(
        id=data.get("id"),
        conversacion_id=data["conversacion_id"],
        autor_id=data["autor_id"],
        autor=data["autor"],
        cuerpo=data["cuerpo"],
        enviado_at=data["enviado_at"].isoformat() if hasattr(data["enviado_at"], "isoformat") else str(data["enviado_at"]),
        **extra,
    )


def _can_access_conversation(cursor, auth_context: dict, conversacion_id: int) -> bool:
    role = (auth_context.get("rol") or "").lower().strip()
    usuario_id = auth_context["id"]

    if role in {"administrador", "admin"}:
        return True

    if role in {"soporte", "operador"}:
        return _repo.conversacion_esta_derivada_a_soporte(cursor, conversacion_id)

    if _repo.conversacion_pertenece_a_usuario(cursor, conversacion_id, usuario_id):
        return True

    if _repo.user_participa_en_conversacion(cursor, conversacion_id, usuario_id):
        return True

    return not _repo.conversacion_tiene_usuario_id(cursor) and not _repo.conversacion_tiene_mensajes(cursor, conversacion_id)


def _ensure_can_access_conversation(cursor, auth_context: dict, conversacion_id: int) -> None:
    if not _can_access_conversation(cursor, auth_context, conversacion_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tenés acceso a esta conversación")


def _ensure_support_role(auth_context: dict) -> None:
    role = (auth_context.get("rol") or "").lower().strip()
    if role not in {"soporte", "operador", "administrador", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso denegado")


def _message_payload(mensaje) -> dict:
    return {
        "id": mensaje.id,
        "conversacion_id": mensaje.conversacion_id,
        "autor_id": mensaje.autor_id,
        "autor": mensaje.autor,
        "cuerpo": mensaje.cuerpo,
        "enviado_at": mensaje.enviado_at.isoformat(),
    }


async def _broadcast_message(conversacion_id: int, mensaje) -> None:
    await ws_manager.broadcast_message(conversacion_id, _message_payload(mensaje))


def _iso(value):
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _motivo_label(motivo: str | None) -> str:
    labels = {
        "solicitud_usuario": "El usuario pidió hablar con una persona.",
        "bot_no_resolvio": "El bot no pudo resolver la consulta.",
    }
    return labels.get(motivo or "", "Derivación a soporte.")


def _resumen_contexto(mensajes: list[dict], motivo: str | None) -> str:
    mensajes_cliente = [
        mensaje["cuerpo"].strip()
        for mensaje in mensajes
        if mensaje.get("autor") in {"usuario", "cliente", "socio"}
        and mensaje.get("cuerpo")
        and mensaje["cuerpo"].strip()
    ]
    if not mensajes_cliente:
        return _motivo_label(motivo)

    primeras_consultas = " ".join(mensajes_cliente[:3])
    if len(primeras_consultas) > 360:
        primeras_consultas = primeras_consultas[:357].rstrip() + "..."
    return f"{_motivo_label(motivo)} Consulta del cliente: {primeras_consultas}"


@router.post("/iniciar", response_model=IniciarConversacionResponse)
def iniciar(payload: IniciarConversacionRequest, authorization: str | None = Header(default=None)):
    auth_context = _get_auth_context(authorization)
    try:
        result = iniciar_conversacion(payload.prompt_key, auth_context["id"])
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return IniciarConversacionResponse(**result)


@router.post("/mensaje", response_model=MensajeResponse)
async def enviar_mensaje(payload: EnviarMensajeRequest, authorization: str | None = Header(default=None)):
    auth_context = _get_auth_context(authorization)
    usuario_id = auth_context["id"]
    role = (auth_context.get("rol") or "").lower().strip()
    prompt_key = payload.prompt_key

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                _ensure_can_access_conversation(cursor, auth_context, payload.conversacion_id)
                if _repo.conversacion_esta_cerrada(cursor, payload.conversacion_id):
                    raise ValueError("La conversación está cerrada")
                bot_id = _repo.get_bot_user_id(cursor)
                fase_actual = _repo.get_fase_estado_by_conversacion_id(cursor, payload.conversacion_id)
                if not prompt_key:
                    prompt_key = _repo.get_prompt_key_by_conversacion_id(cursor, payload.conversacion_id)

        mensaje_usuario = guardar_mensaje(
            conversacion_id=payload.conversacion_id,
            autor_id=usuario_id,
            mensaje={
                "cuerpo": payload.pregunta,
                "autor": role if role in {"soporte", "operador", "cliente", "socio"} else "usuario",
                "enviado_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        await _broadcast_message(payload.conversacion_id, mensaje_usuario)

        if fase_actual == "operario":
            return _mensaje_response_from_dict(
                {
                    "id": mensaje_usuario.id,
                    "conversacion_id": mensaje_usuario.conversacion_id,
                    "autor_id": mensaje_usuario.autor_id,
                    "autor": mensaje_usuario.autor,
                    "cuerpo": mensaje_usuario.cuerpo,
                    "enviado_at": mensaje_usuario.enviado_at,
                },
                fase="operario",
            )

        if prompt_key and requiere_soporte_por_pregunta(payload.pregunta):
            handoff = mensaje_derivacion("solicitud_usuario")
            data = derivar_conversacion_a_soporte(payload.conversacion_id, "solicitud_usuario")
            mensaje_bot = guardar_mensaje(
                conversacion_id=payload.conversacion_id,
                autor_id=bot_id,
                mensaje={
                    "cuerpo": handoff,
                    "autor": "bot",
                    "enviado_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            await _broadcast_message(payload.conversacion_id, mensaje_bot)
            return _mensaje_response_from_dict(
                {
                    "id": mensaje_bot.id,
                    "conversacion_id": mensaje_bot.conversacion_id,
                    "autor_id": mensaje_bot.autor_id,
                    "autor": mensaje_bot.autor,
                    "cuerpo": mensaje_bot.cuerpo,
                    "enviado_at": mensaje_bot.enviado_at,
                },
                requiere_soporte=True,
                fase=data["fase"],
                motivo_derivacion="solicitud_usuario",
                redireccionar_a=f"/chat_soporte.html?conversation_id={payload.conversacion_id}",
            )

        if not prompt_key:
            raise ValueError("No se pudo determinar el tema de la conversación")

        respuesta = ask_bot(payload.pregunta, prompt_key)

        if requiere_soporte_por_respuesta(respuesta["cuerpo"]):
            handoff = mensaje_derivacion("bot_no_resolvio")
            data = derivar_conversacion_a_soporte(payload.conversacion_id, "bot_no_resolvio")
            mensaje_bot = guardar_mensaje(
                conversacion_id=payload.conversacion_id,
                autor_id=bot_id,
                mensaje={
                    "cuerpo": handoff,
                    "autor": "bot",
                    "enviado_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            await _broadcast_message(payload.conversacion_id, mensaje_bot)

            return _mensaje_response_from_dict(
                {
                    "id": mensaje_bot.id,
                    "conversacion_id": mensaje_bot.conversacion_id,
                    "autor_id": mensaje_bot.autor_id,
                    "autor": mensaje_bot.autor,
                    "cuerpo": mensaje_bot.cuerpo,
                    "enviado_at": mensaje_bot.enviado_at,
                },
                requiere_soporte=True,
                fase=data["fase"],
                motivo_derivacion="bot_no_resolvio",
                redireccionar_a=f"/chat_soporte.html?conversation_id={payload.conversacion_id}",
            )

        mensaje_bot = guardar_mensaje(
            conversacion_id=payload.conversacion_id,
            autor_id=bot_id,
            mensaje=respuesta,
        )
        await _broadcast_message(payload.conversacion_id, mensaje_bot)

    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return MensajeResponse(
        id=mensaje_bot.id,
        conversacion_id=mensaje_bot.conversacion_id,
        autor_id=mensaje_bot.autor_id,
        autor=mensaje_bot.autor,
        cuerpo=mensaje_bot.cuerpo,
        enviado_at=mensaje_bot.enviado_at.isoformat(),
    )


@router.get("/conversacion/{conversacion_id}", response_model=ConversacionResponse)
def get_conversacion(conversacion_id: int, authorization: str | None = Header(default=None)):
    auth_context = _get_auth_context(authorization)

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                _ensure_can_access_conversation(cursor, auth_context, conversacion_id)
        conversacion = obtener_conversacion(conversacion_id)
        mensajes = obtener_mensajes_conversacion(conversacion_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    return ConversacionResponse(
        conversacion_id=conversacion["id"],
        tema_id=conversacion["tema_id"],
        fase=conversacion["fase"],
        mensajes=[
            ConversacionMensajeResponse(
                id=mensaje["id"],
                conversacion_id=mensaje["conversacion_id"],
                autor_id=mensaje["autor_id"],
                autor=mensaje["autor"],
                cuerpo=mensaje["cuerpo"],
                enviado_at=mensaje["enviado_at"].isoformat() if hasattr(mensaje["enviado_at"], "isoformat") else str(mensaje["enviado_at"]),
            )
            for mensaje in mensajes
        ],
    )


@router.get("/soporte/activa", response_model=ConversacionResponse)
def get_conversacion_activa_soporte(authorization: str | None = Header(default=None)):
    auth_context = _get_auth_context(authorization)
    _ensure_support_role(auth_context)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            conversacion = _repo.get_conversacion_activa_soporte(cursor)
            if not conversacion:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No hay conversaciones activas")
            mensajes = _repo.get_mensajes_by_conversacion_id(cursor, conversacion["id"])

    return ConversacionResponse(
        conversacion_id=conversacion["id"],
        tema_id=conversacion["tema_id"],
        fase=conversacion["fase"],
        mensajes=[
            ConversacionMensajeResponse(
                id=mensaje["id"],
                conversacion_id=mensaje["conversacion_id"],
                autor_id=mensaje["autor_id"],
                autor=mensaje["autor"],
                cuerpo=mensaje["cuerpo"],
                enviado_at=mensaje["enviado_at"].isoformat() if hasattr(mensaje["enviado_at"], "isoformat") else str(mensaje["enviado_at"]),
            )
            for mensaje in mensajes
        ],
    )


@router.websocket("/ws/{conversacion_id}")
async def websocket_endpoint(websocket: WebSocket, conversacion_id: int, token: str | None = Query(default=None)):
    # token must be provided as query param: ?token=...
    try:
        if not token:
            await websocket.close(code=1008)
            return
        # validate token
        try:
            auth_context = AuthService().get_profile(token)
        except ValueError:
            await websocket.close(code=1008)
            return

        with get_connection() as conn:
            with conn.cursor() as cursor:
                if not _can_access_conversation(cursor, auth_context, conversacion_id):
                    await websocket.close(code=1008)
                    return

        await ws_manager.connect(conversacion_id, websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # we don't expect clients to send data via WS in this simple implementation
                # ignore or log
        except WebSocketDisconnect:
            await ws_manager.disconnect(conversacion_id, websocket)
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("/soporte/lista")
def get_conversaciones_activas_soporte(authorization: str | None = Header(default=None)):
    auth_context = _get_auth_context(authorization)
    _ensure_support_role(auth_context)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            conversaciones = _repo.get_conversaciones_activas_soporte(cursor, limit=100)

    return conversaciones


@router.get("/soporte/contexto/{conversacion_id}")
def get_contexto_soporte(conversacion_id: int, authorization: str | None = Header(default=None)):
    auth_context = _get_auth_context(authorization)
    _ensure_support_role(auth_context)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            _ensure_can_access_conversation(cursor, auth_context, conversacion_id)
            contexto = _repo.get_contexto_soporte(cursor, conversacion_id)
            if not contexto:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada")
            mensajes = _repo.get_mensajes_by_conversacion_id(cursor, conversacion_id)

    return {
        "conversacion_id": contexto["conversacion_id"],
        "fase": contexto["fase"],
        "abierta_at": _iso(contexto["abierta_at"]),
        "cerrada_at": _iso(contexto["cerrada_at"]),
        "tema": contexto["tema"],
        "prompt_key": contexto["prompt_key"],
        "motivo_derivacion": contexto["motivo_derivacion"],
        "motivo_derivacion_label": _motivo_label(contexto["motivo_derivacion"]),
        "asignada_at": _iso(contexto["asignada_at"]),
        "cliente": contexto["cliente"],
        "resumen": _resumen_contexto(mensajes, contexto["motivo_derivacion"]),
        "ultimos_mensajes": [
            {
                "id": mensaje["id"],
                "autor": mensaje["autor"],
                "cuerpo": mensaje["cuerpo"],
                "enviado_at": _iso(mensaje["enviado_at"]),
            }
            for mensaje in mensajes[-6:]
        ],
    }


@router.post("/conversacion/{conversacion_id}/cerrar")
def cerrar(conversacion_id: int, authorization: str | None = Header(default=None)):
    auth_context = _get_auth_context(authorization)
    _ensure_support_role(auth_context)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            _ensure_can_access_conversation(cursor, auth_context, conversacion_id)

    try:
        cerrar_conversacion(conversacion_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    return {"conversacion_id": conversacion_id, "fase": "cerrada"}
