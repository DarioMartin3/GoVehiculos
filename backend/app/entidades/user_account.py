from dataclasses import dataclass


@dataclass
class UserAccount:
    # Modelo de usuario con datos básicos para autenticación.
    id: int
    email: str
    password: str
    rol: str | None
    estado: int | None
    persona_id: int | None
    nombre: str | None = None
    apellido: str | None = None
