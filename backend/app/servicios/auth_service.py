import psycopg2

from app.core.database import get_connection
from app.core.security import create_access_token, verify_password
from app.core.security import decode_access_token, hash_password
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
                            fecha_nacimiento=payload.fecha_nacimiento,
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

    def get_profile(self, token: str) -> dict:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")

        try:
            user_id = int(user_id_raw)
        except (TypeError, ValueError) as error:
            raise ValueError("Token inválido") from error

        profile = self.usuario_repository.get_profile_by_user_id(user_id)
        if not profile:
            raise ValueError("Usuario no encontrado")
        return profile

    def change_password(self, token: str, current_password: str, new_password: str) -> None:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")

        try:
            user_id = int(user_id_raw)
        except (TypeError, ValueError) as error:
            raise ValueError("Token inválido") from error

        stored_password = self.usuario_repository.get_password_hash_by_user_id(user_id)
        if not stored_password:
            raise ValueError("Usuario no encontrado")

        if not verify_password(current_password, stored_password):
            raise ValueError("La contraseña actual es incorrecta")

        if len(new_password) < 8:
            raise ValueError("La nueva contraseña debe tener al menos 8 caracteres")

        if verify_password(new_password, stored_password):
            raise ValueError("La nueva contraseña no puede ser igual a la actual")

        updated = self.usuario_repository.update_password_by_user_id(user_id, hash_password(new_password))
        if not updated:
            raise ValueError("No se pudo actualizar la contraseña")

    def update_profile(self, token: str, email: str | None, telefono: str | None, pais: int | None) -> dict:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")

        try:
            user_id = int(user_id_raw)
        except (TypeError, ValueError) as error:
            raise ValueError("Token inválido") from error

        if not any([email, telefono, pais]):
            raise ValueError("Debe proporcionar al menos un campo para actualizar")

        if email:
            existing_user = self.usuario_repository.get_by_email(email)
            if existing_user and existing_user.id != user_id:
                raise ValueError("El email ya está registrado")

        updated = self.usuario_repository.update_persona_by_user_id(user_id, email, telefono, pais)
        if not updated:
            raise ValueError("No se pudo actualizar el perfil")

        profile = self.usuario_repository.get_profile_by_user_id(user_id)
        if not profile:
            raise ValueError("Usuario no encontrado")

        return profile

    def list_users_directory(self, token: str) -> list[dict]:
        payload = decode_access_token(token)
        role = (payload.get("rol") or "").strip().lower()
        if role not in {"administrador", "admin"}:
            raise ValueError("Permiso denegado")

        return self.usuario_repository.get_users_directory()

    def update_directory_user(self, token: str, user_id: int, data: dict) -> dict:
        payload = decode_access_token(token)
        role = (payload.get("rol") or "").strip().lower()
        if role not in {"administrador", "admin"}:
            raise ValueError("Permiso denegado")

        if data.get('email'):
            existing_user = self.usuario_repository.get_by_email(data['email'])
            if existing_user and existing_user.id != user_id:
                raise ValueError("El email ya está registrado")

        updated = self.usuario_repository.update_user_directory_by_id(user_id, data)
        if not updated:
            raise ValueError("Usuario no encontrado")

        item = self.usuario_repository.get_user_directory_item_by_id(user_id)
        if not item:
            raise ValueError("Usuario no encontrado")

        return item

    def deactivate_directory_user(self, token: str, user_id: int) -> dict:
        payload = decode_access_token(token)
        role = (payload.get("rol") or "").strip().lower()
        if role not in {"administrador", "admin"}:
            raise ValueError("Permiso denegado")

        updated = self.usuario_repository.deactivate_user_by_id(user_id)
        if not updated:
            raise ValueError("Usuario no encontrado")

        item = self.usuario_repository.get_user_directory_item_by_id(user_id)
        if not item:
            raise ValueError("Usuario no encontrado")

        return item

    def activate_directory_user(self, token: str, user_id: int) -> dict:
        payload = decode_access_token(token)
        role = (payload.get("rol") or "").strip().lower()
        if role not in {"administrador", "admin"}:
            raise ValueError("Permiso denegado")

        updated = self.usuario_repository.activate_user_by_id(user_id)
        if not updated:
            raise ValueError("Usuario no encontrado")

        item = self.usuario_repository.get_user_directory_item_by_id(user_id)
        if not item:
            raise ValueError("Usuario no encontrado")

        return item

    @staticmethod
    def translate_register_error(error: Exception) -> str:
        # Traduce errores técnicos de PostgreSQL a mensajes claros.
        if isinstance(error, psycopg2.errors.ForeignKeyViolation):
            return "El pais enviado no existe en la base de datos"
        if isinstance(error, psycopg2.errors.UniqueViolation):
            return "Ya existe un usuario con esos datos"
        return "No se pudo registrar el usuario"
