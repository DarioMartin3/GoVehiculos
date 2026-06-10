from app.core.database import get_connection


class LicenciaRepository:
    def get_tipos_licencia(self) -> list[dict]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nombre FROM tipo_licencia ORDER BY nombre")
                rows = cur.fetchall()
        return [{"id": r[0], "nombre": r[1]} for r in rows]

    def get_tipo_by_nombre(self, nombre: str, cur) -> int | None:
        cur.execute("SELECT id FROM tipo_licencia WHERE nombre = %s", (nombre,))
        row = cur.fetchone()
        return row[0] if row else None

    def crear_carnet(
        self,
        cursor,
        usuario_id: int,
        nombre_titular: str,
        fecha_emision: str | None,
        fecha_vencimiento: str | None,
        imagen: str,
        clases: list[dict],
    ) -> int:
        cursor.execute(
            """INSERT INTO carnet_conducir
               (usuario_id, nombre_titular, fecha_emision, fecha_vencimiento, imagen, estado_validacion_id)
               VALUES (%s, %s, %s, %s, %s, 2) RETURNING id""",
            (usuario_id, nombre_titular, fecha_emision or None, fecha_vencimiento or None, imagen),
        )
        carnet_id = cursor.fetchone()[0]

        for clase in clases:
            tipo_id = self.get_tipo_by_nombre(clase["clase"], cursor)
            if tipo_id:
                cursor.execute(
                    """INSERT INTO carnet_clase
                       (carnet_id, tipo_licencia_id, fecha_otorgamiento, fecha_vencimiento)
                       VALUES (%s, %s, %s, %s)""",
                    (
                        carnet_id,
                        tipo_id,
                        clase.get("fecha_otorgamiento") or None,
                        clase.get("fecha_vencimiento") or None,
                    ),
                )

        return carnet_id

    def get_carnet_by_usuario(self, usuario_id: int) -> dict | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, fecha_emision, fecha_vencimiento, estado_validacion_id
                       FROM carnet_conducir WHERE usuario_id = %s ORDER BY id DESC LIMIT 1""",
                    (usuario_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None

                carnet_id = row[0]
                cur.execute(
                    """SELECT tl.nombre, cc.fecha_otorgamiento, cc.fecha_vencimiento
                       FROM carnet_clase cc
                       JOIN tipo_licencia tl ON tl.id = cc.tipo_licencia_id
                       WHERE cc.carnet_id = %s""",
                    (carnet_id,),
                )
                clases = [
                    {
                        "clase": r[0],
                        "fecha_otorgamiento": str(r[1]) if r[1] else None,
                        "fecha_vencimiento": str(r[2]) if r[2] else None,
                    }
                    for r in cur.fetchall()
                ]

        return {
            "id": carnet_id,
            "fecha_emision": str(row[1]) if row[1] else None,
            "fecha_vencimiento": str(row[2]) if row[2] else None,
            "estado_validacion": row[3],
            "clases": clases,
        }
