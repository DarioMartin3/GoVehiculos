from app.core.database import get_connection
from app.entidades import UserAccount


class UsuarioRepository:
    def create(self, cursor, persona_id: int, password: str, rol: str, estado: int | None) -> int:
        # Crea el usuario enlazado con persona_id y devuelve su id.
        cursor.execute(
            """
            INSERT INTO usuario (persona_id, password, rol, estado)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (persona_id, password, rol, estado),
        )
        return cursor.fetchone()[0]

    def get_by_email(self, email: str) -> UserAccount | None:
        # Busca por email en persona y trae datos de usuario + persona.
        query = """
            SELECT u.id, u.password, u.rol, u.estado, u.persona_id,
                   p.email, p.nombre, p.apellido
            FROM usuario u
            INNER JOIN persona p ON p.id = u.persona_id
            WHERE LOWER(p.email) = LOWER(%s)
            LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (email,))
                row = cursor.fetchone()

        if not row:
            return None

        return UserAccount(
            id=row[0],
            password=row[1],
            rol=row[2],
            estado=row[3],
            persona_id=row[4],
            email=row[5],
            nombre=row[6],
            apellido=row[7],
        )
