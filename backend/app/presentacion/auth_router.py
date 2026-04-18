from fastapi import APIRouter, HTTPException, status

from app.schemas import (
    LoginRequest,
    LoginResponse,
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
