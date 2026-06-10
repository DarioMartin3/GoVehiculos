from app.core.database import get_connection


class DocumentoVehiculoRepository:
    def get_or_create_tipo_id(self, cursor, nombre: str) -> int:
        cursor.execute(
            "SELECT id FROM tipo_documento_vehiculo WHERE LOWER(nombre) = LOWER(%s) LIMIT 1",
            (nombre,),
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute(
            "INSERT INTO tipo_documento_vehiculo (nombre) VALUES (%s) RETURNING id",
            (nombre,),
        )
        return cursor.fetchone()[0]

    def save(
        self,
        cursor,
        vehiculo_id: int,
        tipo_id: int,
        nombre_titular: str,
        imagen: str,
        estado_validacion_id: int,
        fecha_vencimiento: str = "2099-12-31",
    ) -> int:
        cursor.execute(
            """
            INSERT INTO documento_vehiculo
                (vehiculo_id, tipo_id, nombre_titular, fecha_vencimiento, imagen, estado_validacion_id, estado_id)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
            RETURNING id
            """,
            (vehiculo_id, tipo_id, nombre_titular, fecha_vencimiento, imagen, estado_validacion_id),
        )
        return cursor.fetchone()[0]

    def count_by_vehiculo_tipo(self, cursor, vehiculo_id: int, tipo_id: int) -> int:
        cursor.execute(
            "SELECT COUNT(*) FROM documento_vehiculo WHERE vehiculo_id = %s AND tipo_id = %s",
            (vehiculo_id, tipo_id),
        )
        return cursor.fetchone()[0]

    def list_by_vehiculo(self, vehiculo_id: int) -> list[dict]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, vehiculo_id, tipo_id, nombre_titular, imagen, estado_validacion_id, estado_id
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
                "tipo_id": row[2],
                "nombre_titular": row[3],
                "imagen": row[4],
                "estado_validacion_id": row[5],
                "estado_id": row[6],
            }
            for row in rows
        ]
