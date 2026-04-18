from dataclasses import dataclass


@dataclass
class Persona:
    # Representa un registro de la tabla persona.
    id: int | None
    nombre: str
    apellido: str
    email: str
    telefono: str | None = None
    dni: str | None = None
    pais: int | None = None
    estado: int | None = None
