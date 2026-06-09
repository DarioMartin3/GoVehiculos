from datetime import date

from app.core.database import get_connection
from app.entidades.vehiculo import Vehiculo
from app.entidades.vehiculo import VehiculoPatente


class VehiculoRepository:
    def _build_vehicle_entity_from_row(self, row: tuple) -> Vehiculo:
        return Vehiculo(
            id=row[0],
            usuario_id=row[1],
            patente=row[2],
            anio=row[3],
            fecha_ingreso=row[4].isoformat() if row[4] else None,
            estado_vehiculo=row[5],
            modelo_id=row[6],
            modelo_nombre=row[7],
            marca_nombre=row[8],
            foto_vehiculo=row[9] if len(row) > 9 else None,
        )

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

    def get_vehicle_by_patente(self, patente: str) -> VehiculoPatente | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, patente
                    FROM vehiculo
                    WHERE LOWER(patente) = LOWER(%s)
                    LIMIT 1
                    """,
                    (patente,),
                )
                row = cursor.fetchone()

        if not row:
            return None

        return VehiculoPatente(id=row[0], patente=row[1])

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

    def get_vehicle_by_id(self, vehicle_id: int) -> Vehiculo | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT v.id, v.usuario_id, v.patente, v.anio, v.fecha_ingreso,
                           ev.nombre AS estado_vehiculo,
                           m.id AS modelo_id, m.nombre AS modelo_nombre, ma.nombre AS marca_nombre,
                           (SELECT dv.imagen FROM documento_vehiculo dv
                            WHERE dv.vehiculo_id = v.id AND dv.tipo_id = 1
                            ORDER BY dv.id DESC LIMIT 1) AS foto_vehiculo
                    FROM vehiculo v
                    INNER JOIN modelo m ON m.id = v.modelo_id
                    INNER JOIN marca ma ON ma.id = m.marca_id
                    LEFT JOIN estado_vehiculo ev ON ev.id = v.estado_vehiculo_id
                    WHERE v.id = %s
                    LIMIT 1
                    """,
                    (vehicle_id,),
                )
                row = cursor.fetchone()

        if not row:
            return None

        return self._build_vehicle_entity_from_row(row)

    def list_vehicles(self, usuario_id: int | None = None) -> list[Vehiculo]:
        query = """
            SELECT v.id, v.usuario_id, v.patente, v.anio, v.fecha_ingreso,
                   ev.nombre AS estado_vehiculo,
                   m.id AS modelo_id, m.nombre AS modelo_nombre, ma.nombre AS marca_nombre,
                   (SELECT dv.imagen FROM documento_vehiculo dv
                    WHERE dv.vehiculo_id = v.id AND dv.tipo_id = 1
                    ORDER BY dv.id DESC LIMIT 1) AS foto_vehiculo
            FROM vehiculo v
            INNER JOIN modelo m ON m.id = v.modelo_id
            INNER JOIN marca ma ON ma.id = m.marca_id
            LEFT JOIN estado_vehiculo ev ON ev.id = v.estado_vehiculo_id
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

        vehicles: list[Vehiculo] = []
        for row in rows:
            vehicles.append(self._build_vehicle_entity_from_row(row))

        return vehicles

    def consultar_vehiculos_usuario_funcion(self, usuario_id: int) -> list[dict]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT vehiculo_id, patente, anio, fecha_ingreso, estado, modelo, marca
                    FROM consultar_vehiculos_usuario(%s)
                    """,
                    (usuario_id,),
                )
                rows = cursor.fetchall()

        return [
            {
                "vehiculo_id": row[0],
                "patente": row[1],
                "anio": row[2],
                "fecha_ingreso": row[3].isoformat() if row[3] else None,
                "estado": row[4],
                "modelo": row[5],
                "marca": row[6],
            }
            for row in rows
        ]

    def find_or_create_marca(self, cursor, nombre: str) -> int:
        cursor.execute(
            "SELECT id FROM marca WHERE LOWER(nombre) = LOWER(%s) LIMIT 1",
            (nombre.strip(),),
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor.execute("INSERT INTO marca (nombre) VALUES (%s) RETURNING id", (nombre.strip(),))
        return cursor.fetchone()[0]

    def find_or_create_modelo(self, cursor, nombre: str, marca_id: int) -> int:
        cursor.execute(
            "SELECT id FROM modelo WHERE LOWER(nombre) = LOWER(%s) AND marca_id = %s LIMIT 1",
            (nombre.strip(), marca_id),
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor.execute(
            "INSERT INTO modelo (nombre, marca_id) VALUES (%s, %s) RETURNING id",
            (nombre.strip(), marca_id),
        )
        return cursor.fetchone()[0]

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

    def actualizar_estado_vehiculo_procedimiento(self, cursor, vehicle_id: int, estado_nombre: str) -> None:
        cursor.execute(
            "CALL actualizar_estado_vehiculo(%s, %s)",
            (vehicle_id, estado_nombre),
        )
