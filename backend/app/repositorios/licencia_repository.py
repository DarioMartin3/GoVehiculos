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
        usuario_id: int,
        fecha_emision: str | None,
        fecha_vencimiento: str | None,
        clases: list[dict],
    ) -> int:
        with get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """INSERT INTO carnet_conducir
                           (usuario_id, fecha_emision, fecha_vencimiento, estado_validacion)
                           VALUES (%s, %s, %s, 1) RETURNING id""",
                        (usuario_id, fecha_emision or None, fecha_vencimiento or None),
                    )
                    carnet_id = cur.fetchone()[0]

                    for clase in clases:
                        tipo_id = self.get_tipo_by_nombre(clase["clase"], cur)
                        if tipo_id:
                            cur.execute(
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
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
        return carnet_id

    def get_carnet_by_usuario(self, usuario_id: int) -> dict | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, fecha_emision, fecha_vencimiento, estado_validacion
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
