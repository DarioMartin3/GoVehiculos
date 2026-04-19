from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    # Datos que el frontend envía al iniciar sesión.
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    # Datos mínimos del usuario que devolvemos al frontend.
    id: int
    email: EmailStr
    rol: str | None = None
    nombre: str | None = None
    apellido: str | None = None


class LoginResponse(BaseModel):
    # Respuesta del login: token + datos de usuario.
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RegisterUserRequest(BaseModel):
    # Datos necesarios para crear persona y usuario.
    nombre: str
    apellido: str
    email: EmailStr
    telefono: str | None = None
    dni: str | None = None
    pais: int | None = None
    password: str
    rol: str
    estado_usuario: int | None = 1


class RegisterUserResponse(BaseModel):
    # Respuesta del registro exitoso.
    persona_id: int
    user: UserResponse


class ProfileResponse(BaseModel):
    # Datos de perfil extendidos (usuario + persona).
    id: int
    email: EmailStr
    rol: str | None = None
    nombre: str | None = None
    apellido: str | None = None
    telefono: str | None = None
    dni: str | None = None
    pais: str | None = None


class ChangePasswordRequest(BaseModel):
    # Cambio de contraseña para usuario autenticado.
    current_password: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    # Actualización de perfil para usuario autenticado.
    email: EmailStr | None = None
    telefono: str | None = None
    pais: int | None = None
