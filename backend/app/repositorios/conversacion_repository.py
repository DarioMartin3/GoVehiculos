from app.entidades.mensaje import Mensaje


class ConversacionRepository:

    def get_fase_id(self, cursor, estado: str) -> int:
        cursor.execute(
            "SELECT id FROM fase_conversacion WHERE estado = %s LIMIT 1",
            (estado,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Fase de conversación '{estado}' no encontrada")
        return row[0]

    def get_tema_id_by_prompt_key(self, cursor, prompt_key: str) -> int:
        cursor.execute(
            "SELECT id FROM bot_tema WHERE prompt_key = %s AND activo = TRUE LIMIT 1",
            (prompt_key,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Tema con clave '{prompt_key}' no encontrado o inactivo")
        return row[0]

    def get_prompt_key_by_conversacion_id(self, cursor, conversacion_id: int) -> str:
        cursor.execute(
            """
            SELECT bt.prompt_key
            FROM conversacion c
            INNER JOIN bot_tema bt ON bt.id = c.tema_id
            WHERE c.id = %s
            LIMIT 1
            """,
            (conversacion_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Conversación '{conversacion_id}' no encontrada")
        return row[0]

    def conversacion_tiene_usuario_id(self, cursor) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'conversacion'
              AND column_name = 'usuario_id'
            LIMIT 1
            """
        )
        return cursor.fetchone() is not None

    def crear_conversacion(self, cursor, tema_id: int, fase_id: int, usuario_id: int | None = None) -> int:
        if self.conversacion_tiene_usuario_id(cursor):
            cursor.execute(
                """
                INSERT INTO conversacion (fase_id, tema_id, usuario_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (fase_id, tema_id, usuario_id),
            )
            return cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO conversacion (fase_id, tema_id)
            VALUES (%s, %s)
            RETURNING id
            """,
            (fase_id, tema_id),
        )
        return cursor.fetchone()[0]

    def get_conversacion_by_id(self, cursor, conversacion_id: int) -> dict | None:
        cursor.execute(
            """
            SELECT c.id, c.tema_id, fc.estado, c.cerrada_at
            FROM conversacion c
            INNER JOIN fase_conversacion fc ON fc.id = c.fase_id
            WHERE c.id = %s
            LIMIT 1
            """,
            (conversacion_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "tema_id": row[1],
            "fase": row[2],
            "cerrada_at": row[3],
        }

    def get_conversacion_activa_soporte(self, cursor) -> dict | None:
        cursor.execute(
            """
            SELECT c.id, c.tema_id, fc.estado, c.cerrada_at
            FROM conversacion c
            INNER JOIN fase_conversacion fc ON fc.id = c.fase_id
            WHERE c.cerrada_at IS NULL
              AND LOWER(fc.estado) = 'operario'
            ORDER BY c.id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "tema_id": row[1],
            "fase": row[2],
            "cerrada_at": row[3],
        }

    def get_conversaciones_activas_soporte(self, cursor, limit: int = 50) -> list[dict]:
        cursor.execute(
            """
            SELECT
                c.id,
                c.tema_id,
                fc.estado,
                lm.cuerpo AS last_message,
                lm.enviado_at AS last_message_at,
                p.nombre AS persona_nombre,
                p.apellido AS persona_apellido,
                bt.nombre AS tema_nombre,
                d.motivo AS motivo_derivacion,
                d.asignada_at
            FROM conversacion c
            INNER JOIN fase_conversacion fc ON fc.id = c.fase_id
            INNER JOIN bot_tema bt ON bt.id = c.tema_id
            LEFT JOIN LATERAL (
                SELECT m.cuerpo, m.enviado_at, m.autor_id
                FROM mensaje m
                WHERE m.conversacion_id = c.id
                ORDER BY m.enviado_at DESC, m.id DESC
                LIMIT 1
            ) lm ON TRUE
            LEFT JOIN LATERAL (
                SELECT m.autor_id
                FROM mensaje m
                WHERE m.conversacion_id = c.id
                  AND m.autor_id <> (
                    SELECT ub.id
                    FROM usuario ub
                    WHERE ub.persona_id IS NULL AND ub.password IS NULL
                    LIMIT 1
                  )
                ORDER BY m.enviado_at ASC, m.id ASC
                LIMIT 1
            ) fm ON TRUE
            LEFT JOIN LATERAL (
                SELECT de.motivo, de.asignada_at
                FROM derivacion de
                WHERE de.conversacion_id = c.id
                  AND de.liberada_at IS NULL
                ORDER BY de.asignada_at DESC, de.id DESC
                LIMIT 1
            ) d ON TRUE
            LEFT JOIN usuario u ON u.id = fm.autor_id
            LEFT JOIN persona p ON p.id = u.persona_id
            WHERE c.cerrada_at IS NULL
              AND LOWER(fc.estado) = 'operario'
            ORDER BY lm.enviado_at DESC NULLS LAST, c.id DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        results: list[dict] = []
        for row in rows:
            persona_nombre = row[5] or ""
            persona_apellido = row[6] or ""
            cliente = (persona_nombre + " " + persona_apellido).strip() or "Cliente"
            results.append(
                {
                    "id": row[0],
                    "tema_id": row[1],
                    "fase": row[2],
                    "last_message": row[3],
                    "last_message_at": row[4],
                    "cliente": cliente,
                    "tema": row[7],
                    "motivo_derivacion": row[8],
                    "asignada_at": row[9],
                }
            )
        return results

    def get_contexto_soporte(self, cursor, conversacion_id: int) -> dict | None:
        cursor.execute(
            """
            SELECT
                c.id,
                fc.estado,
                c.abierta_at,
                c.cerrada_at,
                bt.nombre AS tema_nombre,
                bt.prompt_key,
                d.motivo,
                d.asignada_at,
                p.nombre AS persona_nombre,
                p.apellido AS persona_apellido,
                p.email AS persona_email,
                p.telefono AS persona_telefono
            FROM conversacion c
            INNER JOIN fase_conversacion fc ON fc.id = c.fase_id
            INNER JOIN bot_tema bt ON bt.id = c.tema_id
            LEFT JOIN LATERAL (
                SELECT de.motivo, de.asignada_at
                FROM derivacion de
                WHERE de.conversacion_id = c.id
                ORDER BY de.asignada_at DESC, de.id DESC
                LIMIT 1
            ) d ON TRUE
            LEFT JOIN LATERAL (
                SELECT m.autor_id
                FROM mensaje m
                WHERE m.conversacion_id = c.id
                  AND m.autor_id <> (
                    SELECT ub.id
                    FROM usuario ub
                    WHERE ub.persona_id IS NULL AND ub.password IS NULL
                    LIMIT 1
                  )
                ORDER BY m.enviado_at ASC, m.id ASC
                LIMIT 1
            ) fm ON TRUE
            LEFT JOIN usuario u ON u.id = fm.autor_id
            LEFT JOIN persona p ON p.id = u.persona_id
            WHERE c.id = %s
            LIMIT 1
            """,
            (conversacion_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        cliente_nombre = ((row[8] or "") + " " + (row[9] or "")).strip() or "Cliente"
        return {
            "conversacion_id": row[0],
            "fase": row[1],
            "abierta_at": row[2],
            "cerrada_at": row[3],
            "tema": row[4],
            "prompt_key": row[5],
            "motivo_derivacion": row[6],
            "asignada_at": row[7],
            "cliente": {
                "nombre": cliente_nombre,
                "email": row[10],
                "telefono": row[11],
            },
        }

    def user_participa_en_conversacion(self, cursor, conversacion_id: int, usuario_id: int) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM mensaje
            WHERE conversacion_id = %s
              AND autor_id = %s
            LIMIT 1
            """,
            (conversacion_id, usuario_id),
        )
        return cursor.fetchone() is not None

    def conversacion_pertenece_a_usuario(self, cursor, conversacion_id: int, usuario_id: int) -> bool:
        if not self.conversacion_tiene_usuario_id(cursor):
            return False

        cursor.execute(
            """
            SELECT 1
            FROM conversacion
            WHERE id = %s
              AND usuario_id = %s
            LIMIT 1
            """,
            (conversacion_id, usuario_id),
        )
        return cursor.fetchone() is not None

    def conversacion_tiene_mensajes(self, cursor, conversacion_id: int) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM mensaje
            WHERE conversacion_id = %s
            LIMIT 1
            """,
            (conversacion_id,),
        )
        return cursor.fetchone() is not None

    def conversacion_esta_derivada_a_soporte(self, cursor, conversacion_id: int) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM conversacion c
            INNER JOIN fase_conversacion fc ON fc.id = c.fase_id
            LEFT JOIN derivacion d ON d.conversacion_id = c.id
            WHERE c.id = %s
              AND (LOWER(fc.estado) = 'operario' OR d.id IS NOT NULL)
            LIMIT 1
            """,
            (conversacion_id,),
        )
        return cursor.fetchone() is not None

    def conversacion_esta_cerrada(self, cursor, conversacion_id: int) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM conversacion c
            INNER JOIN fase_conversacion fc ON fc.id = c.fase_id
            WHERE c.id = %s
              AND (c.cerrada_at IS NOT NULL OR LOWER(fc.estado) = 'cerrada')
            LIMIT 1
            """,
            (conversacion_id,),
        )
        return cursor.fetchone() is not None

    def get_fase_estado_by_conversacion_id(self, cursor, conversacion_id: int) -> str:
        cursor.execute(
            """
            SELECT fc.estado
            FROM conversacion c
            INNER JOIN fase_conversacion fc ON fc.id = c.fase_id
            WHERE c.id = %s
            LIMIT 1
            """,
            (conversacion_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Conversación '{conversacion_id}' no encontrada")
        return row[0]

    def actualizar_fase_conversacion(self, cursor, conversacion_id: int, fase_id: int) -> None:
        cursor.execute(
            """
            UPDATE conversacion
            SET fase_id = %s
            WHERE id = %s
            """,
            (fase_id, conversacion_id),
        )

    def cerrar_conversacion(self, cursor, conversacion_id: int, fase_id: int) -> bool:
        cursor.execute(
            """
            UPDATE conversacion
            SET fase_id = %s,
                cerrada_at = NOW()
            WHERE id = %s
              AND cerrada_at IS NULL
            """,
            (fase_id, conversacion_id),
        )
        return cursor.rowcount > 0

    def get_support_operator_id(self, cursor) -> int:
        cursor.execute(
            """
            SELECT u.id
            FROM usuario u
            INNER JOIN rol r ON r.id = u.rol_id
            WHERE LOWER(r.nombre) = 'soporte'
              AND u.persona_id IS NOT NULL
            ORDER BY u.id ASC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("No se encontró un usuario soporte para derivar la conversación")
        return row[0]

    def crear_derivacion(self, cursor, conversacion_id: int, operario_id: int, motivo: str) -> int:
        cursor.execute(
            """
            INSERT INTO derivacion (conversacion_id, operario_id, motivo)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (conversacion_id, operario_id, motivo),
        )
        return cursor.fetchone()[0]

    def get_mensajes_by_conversacion_id(self, cursor, conversacion_id: int) -> list[dict]:
        cursor.execute(
            """
            SELECT
                m.id,
                m.conversacion_id,
                m.autor_id,
                CASE
                    WHEN u.persona_id IS NULL AND u.password IS NULL THEN 'bot'
                    WHEN LOWER(r.nombre) = 'soporte' THEN 'soporte'
                    WHEN LOWER(r.nombre) = 'operador' THEN 'operario'
                    WHEN LOWER(r.nombre) = 'cliente' THEN 'usuario'
                    WHEN LOWER(r.nombre) = 'socio' THEN 'usuario'
                    ELSE COALESCE(LOWER(r.nombre), 'usuario')
                END AS autor,
                m.cuerpo,
                m.enviado_at
            FROM mensaje m
            LEFT JOIN usuario u ON u.id = m.autor_id
            LEFT JOIN rol r ON r.id = u.rol_id
            WHERE m.conversacion_id = %s
            ORDER BY m.enviado_at ASC, m.id ASC
            """,
            (conversacion_id,),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "conversacion_id": row[1],
                "autor_id": row[2],
                "autor": row[3],
                "cuerpo": row[4],
                "enviado_at": row[5],
            }
            for row in rows
        ]

    def get_bot_user_id(self, cursor) -> int:
        cursor.execute(
            "SELECT id FROM usuario WHERE persona_id IS NULL AND password IS NULL LIMIT 1"
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("Usuario bot no encontrado en la base de datos")
        return row[0]

    def insertar_mensaje(self, cursor, mensaje: Mensaje) -> int:
        cursor.execute(
            """
            INSERT INTO mensaje (conversacion_id, autor_id, cuerpo, enviado_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (mensaje.conversacion_id, mensaje.autor_id, mensaje.cuerpo, mensaje.enviado_at),
        )
        return cursor.fetchone()[0]
