from pydantic import BaseModel, EmailStr, field_validator


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
    fecha_nacimiento: str | None = None
    password: str
    rol: str
    estado_usuario: int | None = 1

    @field_validator('password')
    @classmethod
    def password_min_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return value


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


class DirectoryUserResponse(BaseModel):
    # Datos para el directorio de usuarios.
    id: int
    email: EmailStr
    rol: str | None = None
    nombre: str | None = None
    apellido: str | None = None
    telefono: str | None = None
    estado: int | None = None
    pais: str | None = None


class DirectoryUserUpdateRequest(BaseModel):
    # Actualización de usuario desde el directorio administrativo.
    email: EmailStr | None = None
    nombre: str | None = None
    apellido: str | None = None
    telefono: str | None = None
    pais: int | None = None
    rol: str | None = None
    estado: int | None = None


class VehicleBrandResponse(BaseModel):
    id: int
    nombre: str


class VehicleModelResponse(BaseModel):
    id: int
    nombre: str
    marca_id: int
    marca_nombre: str


class VehicleCreateRequest(BaseModel):
    patente: str
    modelo_id: int
    anio: int


class VehicleUpdateRequest(BaseModel):
    patente: str | None = None
    modelo_id: int | None = None
    anio: int | None = None


class VehicleResponse(BaseModel):
    id: int
    usuario_id: int
    patente: str
    anio: int
    fecha_ingreso: str | None = None
    estado_vehiculo: str | None = None
    modelo_id: int
    modelo_nombre: str
    marca_nombre: str
    foto_vehiculo: str | None = None


class VehicleRegisterResponse(VehicleResponse):
    nuevo_token: str | None = None


class CedulaVehiculoExtractResponse(BaseModel):
    marca: str
    modelo: str
    patente: str
    anio: int | None = None
    modelo_id: int


class CedulaTitularValidacionResponse(BaseModel):
    valido: bool
    campos_detectados: dict
    coincidencias: dict
    mensaje: str


class SeguroValidacionResponse(BaseModel):
    valido: bool
    campos_detectados: dict
    coincidencias: dict
    mensaje: str


class DocumentoVehiculoResponse(BaseModel):
    id: int
    tipo: str
    imagen: str


class IniciarConversacionRequest(BaseModel):
    prompt_key: str


class IniciarConversacionResponse(BaseModel):
    conversacion_id: int
    tema_id: int
    fase: str


class EnviarMensajeRequest(BaseModel):
    conversacion_id: int
    pregunta: str
    prompt_key: str | None = None


class MensajeResponse(BaseModel):
    id: int | None = None
    conversacion_id: int
    autor_id: int
    autor: str
    cuerpo: str
    enviado_at: str
    requiere_soporte: bool = False
    fase: str | None = None
    motivo_derivacion: str | None = None
    redireccionar_a: str | None = None


class ConversacionMensajeResponse(BaseModel):
    id: int | None = None
    conversacion_id: int
    autor_id: int
    autor: str
    cuerpo: str
    enviado_at: str


class ConversacionResponse(BaseModel):
    conversacion_id: int
    tema_id: int
    fase: str
    mensajes: list[ConversacionMensajeResponse]
