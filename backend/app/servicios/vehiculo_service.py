import re

from app.core.security import decode_access_token
from app.core.database import get_connection
from app.repositorios.usuario_repository import UsuarioRepository
from app.repositorios.vehiculo_repository import VehiculoRepository


class VehiculoService:
    def __init__(self, vehiculo_repository: VehiculoRepository | None = None):
        self.vehiculo_repository = vehiculo_repository or VehiculoRepository()
        self.usuario_repository = UsuarioRepository()

    def list_marcas(self) -> list[dict]:
        return self.vehiculo_repository.get_marcas()

    def list_modelos(self, marca_id: int | None = None) -> list[dict]:
        return self.vehiculo_repository.get_modelos(marca_id)

    def register_vehicle(self, token: str, patente: str, modelo_id: int, anio: int) -> dict:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")
        role = (payload.get("rol") or "").strip().lower()

        if role not in {"socio", "administrador", "admin"}:
            raise ValueError("Permiso denegado")

        try:
            usuario_id = int(user_id_raw)
        except (TypeError, ValueError) as error:
            raise ValueError("Token inválido") from error

        patente_normalizada = patente.strip().upper()
        if not re.fullmatch(r"[A-Z0-9]{6,10}", patente_normalizada):
            raise ValueError("La patente debe tener entre 6 y 10 caracteres alfanuméricos sin espacios ni símbolos")

        if anio < 1980:
            raise ValueError("El año del vehículo no es válido")

        existing_vehicle = self.vehiculo_repository.get_vehicle_by_patente(patente_normalizada)
        if existing_vehicle:
            raise ValueError("Ya existe un vehículo con esa patente")

        modelo = self.vehiculo_repository.get_modelo_by_id(modelo_id)
        if not modelo:
            raise ValueError("El modelo seleccionado no existe")

        with get_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    vehicle_id = self.vehiculo_repository.create_vehicle(
                        cursor,
                        usuario_id=usuario_id,
                        modelo_id=modelo_id,
                        anio=anio,
                        patente=patente_normalizada,
                    )
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise

        vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("No se pudo registrar el vehículo")

        return vehicle