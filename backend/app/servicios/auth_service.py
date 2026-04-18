import psycopg2

from app.core.database import get_connection
from app.core.security import create_access_token, verify_password
from app.core.security import hash_password
from app.entidades import Persona
from app.repositorios.persona_repository import PersonaRepository
from app.repositorios.usuario_repository import UsuarioRepository
from app.schemas import RegisterUserRequest


class AuthService:
    """Lógica de negocio para autenticación y registro de usuarios."""

    def __init__(self, usuario_repository: UsuarioRepository | None = None):
        self.usuario_repository = usuario_repository or UsuarioRepository()
        self.persona_repository = PersonaRepository()

    def login(self, email: str, password: str) -> dict:
        # 1) Buscar usuario por email.
        user = self.usuario_repository.get_by_email(email)
        if not user:
            raise ValueError("Credenciales inválidas")

        # 2) Validar si el usuario está activo (estado=1).
        if user.estado is not None and user.estado != 1:
            raise ValueError("Usuario inactivo")

        # 3) Validar contraseña.
        if not verify_password(password, user.password):
            raise ValueError("Credenciales inválidas")

        # 4) Generar token JWT para sesión.
        token = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email, "rol": user.rol},
        )
        return {
            "access_token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "rol": user.rol,
                "nombre": user.nombre,
                "apellido": user.apellido,
            },
        }

    def register_user(self, payload: RegisterUserRequest) -> dict:
        # Regla de negocio: email no puede repetirse.
        existing_user = self.usuario_repository.get_by_email(payload.email)
        if existing_user:
            raise ValueError("Ya existe un usuario con ese email")

        # Transacción: si falla una parte, se revierte todo.
        with get_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    # Paso 1: crear persona.
                    persona_id = self.persona_repository.create(
                        cursor,
                        Persona(
                            id=None,
                            nombre=payload.nombre,
                            apellido=payload.apellido,
                            email=payload.email,
                            telefono=payload.telefono,
                            dni=payload.dni,
                            pais=payload.pais,
                            estado=payload.estado_persona,
                        ),
                    )

                    # Paso 2: crear usuario asociado a la persona.
                    user_id = self.usuario_repository.create(
                        cursor,
                        persona_id=persona_id,
                        password=hash_password(payload.password),
                        rol=payload.rol,
                        estado=payload.estado_usuario,
                    )

                    # Paso 3: confirmar cambios.
                    connection.commit()
                except Exception:
                    # Si algo sale mal, se deshacen ambos inserts.
                    connection.rollback()
                    raise

        return {
            "persona_id": persona_id,
            "user": {
                "id": user_id,
                "email": payload.email,
                "rol": payload.rol,
                "nombre": payload.nombre,
                "apellido": payload.apellido,
            },
        }

    @staticmethod
    def translate_register_error(error: Exception) -> str:
        # Traduce errores técnicos de PostgreSQL a mensajes claros.
        if isinstance(error, psycopg2.errors.ForeignKeyViolation):
            return "El pais o estado enviado no existe en la base de datos"
        if isinstance(error, psycopg2.errors.UniqueViolation):
            return "Ya existe un usuario con esos datos"
        return "No se pudo registrar el usuario"
