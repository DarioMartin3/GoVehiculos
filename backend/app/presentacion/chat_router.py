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
    derivar_conversacion_a_soporte,
    guardar_mensaje,
    iniciar_conversacion,
    obtener_conversacion,
    obtener_mensajes_conversacion,
)
from app.core.database import get_connection
import asyncio
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


@router.post("/iniciar", response_model=IniciarConversacionResponse)
def iniciar(payload: IniciarConversacionRequest, authorization: str | None = Header(default=None)):
    _get_auth_context(authorization)
    try:
        result = iniciar_conversacion(payload.prompt_key)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return IniciarConversacionResponse(**result)


@router.post("/mensaje", response_model=MensajeResponse)
def enviar_mensaje(payload: EnviarMensajeRequest, authorization: str | None = Header(default=None)):
    auth_context = _get_auth_context(authorization)
    usuario_id = auth_context["id"]
    role = (auth_context.get("rol") or "").lower().strip()
    prompt_key = payload.prompt_key

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
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

        # notify websocket clients (async)
        try:
            asyncio.get_event_loop().create_task(
                ws_manager.broadcast_message(payload.conversacion_id, {
                    "id": mensaje_usuario.id,
                    "conversacion_id": mensaje_usuario.conversacion_id,
                    "autor_id": mensaje_usuario.autor_id,
                    "autor": mensaje_usuario.autor,
                    "cuerpo": mensaje_usuario.cuerpo,
                    "enviado_at": mensaje_usuario.enviado_at.isoformat(),
                })
            )
        except Exception:
            pass

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
            try:
                asyncio.get_event_loop().create_task(
                    ws_manager.broadcast_message(payload.conversacion_id, {
                        "id": mensaje_bot.id,
                        "conversacion_id": mensaje_bot.conversacion_id,
                        "autor_id": mensaje_bot.autor_id,
                        "autor": mensaje_bot.autor,
                        "cuerpo": mensaje_bot.cuerpo,
                        "enviado_at": mensaje_bot.enviado_at.isoformat(),
                    })
                )
            except Exception:
                pass
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
        try:
            asyncio.get_event_loop().create_task(
                ws_manager.broadcast_message(payload.conversacion_id, {
                    "id": mensaje_bot.id,
                    "conversacion_id": mensaje_bot.conversacion_id,
                    "autor_id": mensaje_bot.autor_id,
                    "autor": mensaje_bot.autor,
                    "cuerpo": mensaje_bot.cuerpo,
                    "enviado_at": mensaje_bot.enviado_at.isoformat(),
                })
            )
        except Exception:
            pass

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
    _get_auth_context(authorization)

    try:
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
    _get_auth_context(authorization)

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
            AuthService().get_profile(token)
        except ValueError:
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
    _get_auth_context(authorization)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            conversaciones = _repo.get_conversaciones_activas_soporte(cursor, limit=100)

    return conversaciones
