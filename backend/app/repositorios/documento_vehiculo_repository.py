from app.core.database import get_connection


class DocumentoVehiculoRepository:
    def save(
        self,
        cursor,
        vehiculo_id: int,
        tipo: str,
        nombre_titular: str,
        imagen: str,
        estado_validacion: int,
    ) -> int:
        cursor.execute(
            """
            INSERT INTO documento_vehiculo
                (vehiculo_id, tipo, nombre_titular, imagen, estado_validacion, estado)
            VALUES (%s, %s, %s, %s, %s, 1)
            RETURNING id
            """,
            (vehiculo_id, tipo, nombre_titular, imagen, estado_validacion),
        )
        return cursor.fetchone()[0]

    def count_by_vehiculo_tipo(self, cursor, vehiculo_id: int, tipo: str) -> int:
        cursor.execute(
            "SELECT COUNT(*) FROM documento_vehiculo WHERE vehiculo_id = %s AND tipo = %s",
            (vehiculo_id, tipo),
        )
        return cursor.fetchone()[0]

    def list_by_vehiculo(self, vehiculo_id: int) -> list[dict]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, vehiculo_id, tipo, nombre_titular, imagen, estado_validacion, estado
                    FROM documento_vehiculo
                    WHERE vehiculo_id = %s
                    ORDER BY id ASC
                    """,
                    (vehiculo_id,),
                )
                rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "vehiculo_id": row[1],
                "tipo": row[2],
                "nombre_titular": row[3],
                "imagen": row[4],
                "estado_validacion": row[5],
                "estado": row[6],
            }
            for row in rows
        ]
