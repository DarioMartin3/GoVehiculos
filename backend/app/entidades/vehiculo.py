from dataclasses import dataclass


@dataclass
class Vehiculo:
    # Entidad de dominio para un vehículo con datos enriquecidos para la API.
    id: int
    usuario_id: int
    patente: str
    anio: int
    fecha_ingreso: str | None
    estado_vehiculo: str | None
    modelo_id: int
    modelo_nombre: str
    marca_nombre: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "patente": self.patente,
            "anio": self.anio,
            "fecha_ingreso": self.fecha_ingreso,
            "estado_vehiculo": self.estado_vehiculo,
            "modelo_id": self.modelo_id,
            "modelo_nombre": self.modelo_nombre,
            "marca_nombre": self.marca_nombre,
        }


@dataclass
class VehiculoPatente:
    # Entidad liviana para búsquedas de unicidad por patente.
    id: int
    patente: str