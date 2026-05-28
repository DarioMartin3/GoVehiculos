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

    def crear_conversacion(self, cursor, tema_id: int, fase_id: int) -> int:
        cursor.execute(
            """
            INSERT INTO conversacion (fase_id, tema_id)
            VALUES (%s, %s)
            RETURNING id
            """,
            (fase_id, tema_id),
        )
        return cursor.fetchone()[0]

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
