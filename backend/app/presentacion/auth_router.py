from fastapi import APIRouter, Header, HTTPException, UploadFile, File, Form, status

from app.schemas import (
    ChangePasswordRequest,
    DirectoryUserResponse,
    DirectoryUserUpdateRequest,
    LoginRequest,
    LoginResponse,
    ProfileResponse,
    RegisterUserRequest,
    RegisterUserResponse,
    UpdateProfileRequest,
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


@router.post("/validate-document")
async def validate_document(
    documento: UploadFile = File(...),
    nombre: str = Form(...),
    apellido: str = Form(...),
    dni: str = Form(...),
    fecha_nacimiento: str = Form(...),
):
    from app.servicios.document_validation_service import DocumentValidationService

    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if documento.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato no soportado. Usá JPG, PNG o WEBP.")

    imagen_bytes = await documento.read()
    if len(imagen_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen no puede superar los 5MB.")

    try:
        result = DocumentValidationService().validate(
            image_bytes=imagen_bytes,
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            fecha_nacimiento=fecha_nacimiento,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        print(f"[validate-document ERROR] {type(error).__name__}: {error}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudo conectar con el servicio de validación.") from error

    return result


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


@router.put("/profile")
def update_profile(payload: UpdateProfileRequest, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        result = AuthService().update_profile(token, payload.email, payload.telefono, payload.pais)
    except ValueError as error:
        message = str(error)
        if message == "Usuario no encontrado":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from error
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error

    return ProfileResponse(**result)


@router.get("/users", response_model=list[DirectoryUserResponse])
def list_users_directory(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        result = AuthService().list_users_directory(token)
    except ValueError as error:
        message = str(error)
        if message == "Permiso denegado":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from error
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error

    return [DirectoryUserResponse(**item) for item in result]


@router.put("/users/{user_id}", response_model=DirectoryUserResponse)
def update_directory_user(user_id: int, payload: DirectoryUserUpdateRequest, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        result = AuthService().update_directory_user(token, user_id, payload.model_dump(exclude_unset=True))
    except ValueError as error:
        message = str(error)
        if message == "Permiso denegado":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from error
        if message == "Usuario no encontrado":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from error
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error

    return DirectoryUserResponse(**result)


@router.delete("/users/{user_id}", response_model=DirectoryUserResponse)
def deactivate_directory_user(user_id: int, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        result = AuthService().deactivate_directory_user(token, user_id)
    except ValueError as error:
        message = str(error)
        if message == "Permiso denegado":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from error
        if message == "Usuario no encontrado":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from error
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error

    return DirectoryUserResponse(**result)


@router.post("/users/{user_id}/activate", response_model=DirectoryUserResponse)
def activate_directory_user(user_id: int, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        result = AuthService().activate_directory_user(token, user_id)
    except ValueError as error:
        message = str(error)
        if message == "Permiso denegado":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from error
        if message == "Usuario no encontrado":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from error
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error

    return DirectoryUserResponse(**result)


@router.get("/paises")
def get_countries():
    from app.core.database import get_connection

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, nombre FROM pais ORDER BY nombre ASC")
            rows = cursor.fetchall()

    countries = [{"id": row[0], "nombre": row[1]} for row in rows]
    return countries
