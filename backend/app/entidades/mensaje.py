from dataclasses import dataclass
from datetime import datetime


@dataclass
class Mensaje:
    conversacion_id: int
    autor_id: int
    cuerpo: str
    enviado_at: datetime
    id: int | None = None
    autor: str | None = None
