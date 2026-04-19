from datetime import date

from app.core.database import get_connection


class VehiculoRepository:
    def _get_estado_vehiculo_id(self, cursor, estado_nombre: str) -> int:
        cursor.execute(
            """
            SELECT id
            FROM estado_vehiculo
            WHERE LOWER(nombre) = LOWER(%s)
            LIMIT 1
            """,
            (estado_nombre,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("El estado del vehículo no existe en la base de datos")
        return row[0]

    def get_marcas(self) -> list[dict]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, nombre
                    FROM marca
                    ORDER BY nombre ASC
                    """
                )
                rows = cursor.fetchall()

        return [{"id": row[0], "nombre": row[1]} for row in rows]

    def get_modelos(self, marca_id: int | None = None) -> list[dict]:
        query = """
            SELECT m.id, m.nombre, ma.id AS marca_id, ma.nombre AS marca_nombre
            FROM modelo m
            INNER JOIN marca ma ON ma.id = m.marca_id
        """
        params: tuple[object, ...] = ()
        if marca_id is not None:
            query += " WHERE m.marca_id = %s"
            params = (marca_id,)

        query += " ORDER BY ma.nombre ASC, m.nombre ASC"

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "nombre": row[1],
                "marca_id": row[2],
                "marca_nombre": row[3],
            }
            for row in rows
        ]

    def get_modelo_by_id(self, modelo_id: int) -> dict | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT m.id, m.nombre, ma.id AS marca_id, ma.nombre AS marca_nombre
                    FROM modelo m
                    INNER JOIN marca ma ON ma.id = m.marca_id
                    WHERE m.id = %s
                    LIMIT 1
                    """,
                    (modelo_id,),
                )
                row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "nombre": row[1],
            "marca_id": row[2],
            "marca_nombre": row[3],
        }

    def get_vehicle_by_patente(self, patente: str) -> dict | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM vehiculo
                    WHERE LOWER(patente) = LOWER(%s)
                    LIMIT 1
                    """,
                    (patente,),
                )
                row = cursor.fetchone()

        if not row:
            return None

        return {"id": row[0]}

    def create_vehicle(self, cursor, usuario_id: int, modelo_id: int, anio: int, patente: str) -> int:
        estado_vehiculo_id = self._get_estado_vehiculo_id(cursor, "En validacion")
        cursor.execute(
            """
            INSERT INTO vehiculo (usuario_id, modelo, anio, fecha_ingreso, patente, estado_vehiculo)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (usuario_id, modelo_id, anio, date.today(), patente, estado_vehiculo_id),
        )
        return cursor.fetchone()[0]

    def get_vehicle_by_id(self, vehicle_id: int) -> dict | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT v.id, v.usuario_id, v.patente, v.anio, v.fecha_ingreso,
                           ev.nombre AS estado_vehiculo,
                           m.id AS modelo_id, m.nombre AS modelo_nombre, ma.nombre AS marca_nombre
                    FROM vehiculo v
                    INNER JOIN modelo m ON m.id = v.modelo
                    INNER JOIN marca ma ON ma.id = m.marca_id
                    LEFT JOIN estado_vehiculo ev ON ev.id = v.estado_vehiculo
                    WHERE v.id = %s
                    LIMIT 1
                    """,
                    (vehicle_id,),
                )
                row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "usuario_id": row[1],
            "patente": row[2],
            "anio": row[3],
            "fecha_ingreso": row[4].isoformat() if row[4] else None,
            "estado_vehiculo": row[5],
            "modelo_id": row[6],
            "modelo_nombre": row[7],
            "marca_nombre": row[8],
        }

    def list_vehicles(self, usuario_id: int | None = None) -> list[dict]:
        query = """
            SELECT v.id, v.usuario_id, v.patente, v.anio, v.fecha_ingreso,
                   ev.nombre AS estado_vehiculo,
                   m.id AS modelo_id, m.nombre AS modelo_nombre, ma.nombre AS marca_nombre
            FROM vehiculo v
            INNER JOIN modelo m ON m.id = v.modelo
            INNER JOIN marca ma ON ma.id = m.marca_id
            LEFT JOIN estado_vehiculo ev ON ev.id = v.estado_vehiculo
        """
        params: tuple[object, ...] = ()

        if usuario_id is not None:
            query += " WHERE v.usuario_id = %s"
            params = (usuario_id,)

        query += " ORDER BY v.fecha_ingreso DESC, v.id DESC"

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        vehicles: list[dict] = []
        for row in rows:
            vehicles.append(
                {
                    "id": row[0],
                    "usuario_id": row[1],
                    "patente": row[2],
                    "anio": row[3],
                    "fecha_ingreso": row[4].isoformat() if row[4] else None,
                    "estado_vehiculo": row[5],
                    "modelo_id": row[6],
                    "modelo_nombre": row[7],
                    "marca_nombre": row[8],
                }
            )

        return vehicles

    def update_vehicle_by_id(self, cursor, vehicle_id: int, data: dict) -> bool:
        updates: list[str] = []
        values: list[object] = []

        if data.get("patente") is not None:
            updates.append("patente = %s")
            values.append(data["patente"])
        if data.get("anio") is not None:
            updates.append("anio = %s")
            values.append(data["anio"])
        if data.get("modelo_id") is not None:
            updates.append("modelo = %s")
            values.append(data["modelo_id"])

        if not updates:
            return True

        values.append(vehicle_id)
        update_clause = ", ".join(updates)

        cursor.execute(
            f"""
            UPDATE vehiculo
            SET {update_clause}
            WHERE id = %s
            """,
            tuple(values),
        )
        return cursor.rowcount > 0

    def update_vehicle_status_by_id(self, cursor, vehicle_id: int, estado_nombre: str) -> bool:
        estado_id = self._get_estado_vehiculo_id(cursor, estado_nombre)
        cursor.execute(
            """
            UPDATE vehiculo
            SET estado_vehiculo = %s
            WHERE id = %s
            """,
            (estado_id, vehicle_id),
        )
        return cursor.rowcount > 0