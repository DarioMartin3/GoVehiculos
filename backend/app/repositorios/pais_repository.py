from app.core.database import get_connection


class PaisRepository:
    def get_paises(self) -> list[dict]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, nombre FROM pais ORDER BY nombre ASC")
                rows = cursor.fetchall()
        return [{"id": row[0], "nombre": row[1]} for row in rows]
