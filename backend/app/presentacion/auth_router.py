from fastapi import APIRouter, Header, HTTPException, status

from app.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    ProfileResponse,
    RegisterUserRequest,
    RegisterUserResponse,
    UserResponse,
)
from app.servicios.auth_service import AuthService

# Esta capa define endpoints HTTP y transforma errores de negocio
# en respuestas entendibles para el cliente.
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    # Delega la lógica al servicio (no accede a DB directamente).
    try:
        result = AuthService().login(payload.email, payload.password)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error

    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
        "user": UserResponse(**result["user"]),
    }


@router.post("/register", response_model=RegisterUserResponse)
def register(payload: RegisterUserRequest):
    # Crea persona + usuario en una transacción controlada por el servicio.
    try:
        result = AuthService().register_user(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        detail = AuthService.translate_register_error(error)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from error

    return {
        "persona_id": result["persona_id"],
        "user": UserResponse(**result["user"]),
    }


@router.get("/profile", response_model=ProfileResponse)
def profile(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        result = AuthService().get_profile(token)
    except ValueError as error:
        message = str(error)
        if message == "Usuario no encontrado":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from error
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error

    return ProfileResponse(**result)


@router.post("/change-password")
@router.post("/change_password")
def change_password(payload: ChangePasswordRequest, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        AuthService().change_password(token, payload.current_password, payload.new_password)
    except ValueError as error:
        message = str(error)
        if message == "Usuario no encontrado":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from error
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error

    return {"message": "Contraseña actualizada correctamente"}
