from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, status

from app.schemas import (
    EnviarMensajeRequest,
    IniciarConversacionRequest,
    IniciarConversacionResponse,
    MensajeResponse,
)
from app.servicios.auth_service import AuthService
from app.servicios.chat_service import ask_bot
from app.servicios.conversacion_service import guardar_mensaje, iniciar_conversacion
from app.core.database import get_connection
from app.repositorios.conversacion_repository import ConversacionRepository

router = APIRouter(prefix="/chat", tags=["chat"])

_repo = ConversacionRepository()


def _get_user_id(authorization: str | None) -> int:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    token = authorization.split(" ", 1)[1].strip()
    try:
        result = AuthService().get_profile(token)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error
    return result["id"]


@router.post("/iniciar", response_model=IniciarConversacionResponse)
def iniciar(payload: IniciarConversacionRequest, authorization: str | None = Header(default=None)):
    _get_user_id(authorization)
    try:
        result = iniciar_conversacion(payload.prompt_key)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return IniciarConversacionResponse(**result)


@router.post("/mensaje", response_model=MensajeResponse)
def enviar_mensaje(payload: EnviarMensajeRequest, authorization: str | None = Header(default=None)):
    usuario_id = _get_user_id(authorization)

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                bot_id = _repo.get_bot_user_id(cursor)

        mensaje_usuario = guardar_mensaje(
            conversacion_id=payload.conversacion_id,
            autor_id=usuario_id,
            mensaje={
                "cuerpo": payload.pregunta,
                "autor": "usuario",
                "enviado_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        respuesta = ask_bot(payload.pregunta, payload.prompt_key)

        mensaje_bot = guardar_mensaje(
            conversacion_id=payload.conversacion_id,
            autor_id=bot_id,
            mensaje=respuesta,
        )

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
