import re

from app.core.security import decode_access_token
from app.core.database import get_connection
from app.entidades.vehiculo import Vehiculo
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

    def _get_request_context(self, token: str) -> tuple[int, str]:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")
        role = (payload.get("rol") or "").strip().lower()

        try:
            usuario_id = int(user_id_raw)
        except (TypeError, ValueError) as error:
            raise ValueError("Token inválido") from error

        return usuario_id, role

    def _vehicle_to_dict(self, vehicle: Vehiculo) -> dict:
        return vehicle.to_dict()

    def _vehicles_to_dict(self, vehicles: list[Vehiculo]) -> list[dict]:
        return [vehicle.to_dict() for vehicle in vehicles]

    def _validate_vehicle_access(self, role: str, vehicle: Vehiculo, usuario_id: int) -> None:
        if role in {"administrador", "admin", "operador", "soporte"}:
            return

        if role == "socio" and vehicle.usuario_id == usuario_id:
            return

        raise ValueError("Permiso denegado")

    def list_vehicles(self, token: str) -> list[dict]:
        usuario_id, role = self._get_request_context(token)

        if role in {"administrador", "admin", "operador", "soporte"}:
            return self._vehicles_to_dict(self.vehiculo_repository.list_vehicles())

        if role == "socio":
            return self._vehicles_to_dict(self.vehiculo_repository.list_vehicles(usuario_id=usuario_id))

        raise ValueError("Permiso denegado")

    def register_vehicle(self, token: str, patente: str, modelo_id: int, anio: int) -> dict:
        usuario_id, role = self._get_request_context(token)

        if role not in {"socio", "administrador", "admin"}:
            raise ValueError("Permiso denegado")

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

        return self._vehicle_to_dict(vehicle)

    def update_vehicle(self, token: str, vehicle_id: int, data: dict) -> dict:
        usuario_id, role = self._get_request_context(token)

        vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("Vehículo no encontrado")

        self._validate_vehicle_access(role, vehicle, usuario_id)

        payload: dict[str, object] = {}

        if data.get("patente") is not None:
            patente = str(data["patente"]).strip().upper()
            if not re.fullmatch(r"[A-Z0-9]{6,10}", patente):
                raise ValueError("La patente debe tener entre 6 y 10 caracteres alfanuméricos sin espacios ni símbolos")

            existing_vehicle = self.vehiculo_repository.get_vehicle_by_patente(patente)
            if existing_vehicle and existing_vehicle.id != vehicle_id:
                raise ValueError("Ya existe un vehículo con esa patente")

            payload["patente"] = patente

        if data.get("anio") is not None:
            try:
                anio = int(data["anio"])
            except (TypeError, ValueError) as error:
                raise ValueError("El año del vehículo no es válido") from error
            if anio < 1980:
                raise ValueError("El año del vehículo no es válido")
            payload["anio"] = anio

        if data.get("modelo_id") is not None:
            try:
                modelo_id = int(data["modelo_id"])
            except (TypeError, ValueError) as error:
                raise ValueError("El modelo seleccionado no existe") from error

            modelo = self.vehiculo_repository.get_modelo_by_id(modelo_id)
            if not modelo:
                raise ValueError("El modelo seleccionado no existe")
            payload["modelo_id"] = modelo_id

        if not payload:
            raise ValueError("Debe proporcionar al menos un campo para actualizar")

        with get_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    updated = self.vehiculo_repository.update_vehicle_by_id(cursor, vehicle_id, payload)
                    if not updated:
                        raise ValueError("Vehículo no encontrado")
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise

        updated_vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not updated_vehicle:
            raise ValueError("Vehículo no encontrado")

        return self._vehicle_to_dict(updated_vehicle)

    def deactivate_vehicle(self, token: str, vehicle_id: int) -> dict:
        usuario_id, role = self._get_request_context(token)

        vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("Vehículo no encontrado")

        self._validate_vehicle_access(role, vehicle, usuario_id)

        with get_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    updated = self.vehiculo_repository.update_vehicle_status_by_id(cursor, vehicle_id, "Inactivo")
                    if not updated:
                        raise ValueError("Vehículo no encontrado")
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise

        updated_vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not updated_vehicle:
            raise ValueError("Vehículo no encontrado")

        return self._vehicle_to_dict(updated_vehicle)

    def activate_vehicle(self, token: str, vehicle_id: int) -> dict:
        usuario_id, role = self._get_request_context(token)

        vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("Vehículo no encontrado")

        self._validate_vehicle_access(role, vehicle, usuario_id)

        with get_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    updated = self.vehiculo_repository.update_vehicle_status_by_id(cursor, vehicle_id, "Activo")
                    if not updated:
                        raise ValueError("Vehículo no encontrado")
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise

        updated_vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not updated_vehicle:
            raise ValueError("Vehículo no encontrado")

        return self._vehicle_to_dict(updated_vehicle)