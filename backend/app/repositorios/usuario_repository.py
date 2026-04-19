from app.core.database import get_connection
from app.entidades import UserAccount


class UsuarioRepository:
    def _usuario_has_column(self, cursor, column_name: str) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'usuario'
              AND column_name = %s
            LIMIT 1
            """,
            (column_name,),
        )
        return cursor.fetchone() is not None

    def create(self, cursor, persona_id: int, password: str, rol: str, estado: int | None) -> int:
        # Crea el usuario enlazado con persona_id y devuelve su id.
        # Soporta ambos esquemas: usuario.rol (texto) y usuario.rol_id (FK a tabla rol).
        if self._usuario_has_column(cursor, 'rol'):
            cursor.execute(
                """
                INSERT INTO usuario (persona_id, password, rol, estado)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (persona_id, password, rol, estado),
            )
            return cursor.fetchone()[0]

        rol_id = self._get_rol_id(cursor, rol)
        cursor.execute(
            """
            INSERT INTO usuario (persona_id, password, rol_id, estado)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (persona_id, password, rol_id, estado),
        )
        return cursor.fetchone()[0]

    def _get_rol_id(self, cursor, rol: str) -> int:
        cursor.execute(
            """
            SELECT id
            FROM rol
            WHERE LOWER(nombre) = LOWER(%s)
            LIMIT 1
            """,
            (rol,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("El rol enviado no existe en la base de datos")
        return row[0]

    def get_by_email(self, email: str) -> UserAccount | None:
        # Busca por email en persona y trae datos de usuario + persona.
        query_with_rol_text = """
            SELECT u.id, u.password, u.rol, u.estado, u.persona_id,
                   p.email, p.nombre, p.apellido
            FROM usuario u
            INNER JOIN persona p ON p.id = u.persona_id
            WHERE LOWER(p.email) = LOWER(%s)
            LIMIT 1
        """
        query_with_rol_fk = """
            SELECT u.id, u.password, r.nombre AS rol, u.estado, u.persona_id,
                   p.email, p.nombre, p.apellido
            FROM usuario u
            INNER JOIN persona p ON p.id = u.persona_id
            LEFT JOIN rol r ON r.id = u.rol_id
            WHERE LOWER(p.email) = LOWER(%s)
            LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                if self._usuario_has_column(cursor, 'rol'):
                    cursor.execute(query_with_rol_text, (email,))
                    row = cursor.fetchone()
                else:
                    cursor.execute(query_with_rol_fk, (email,))
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

    def get_profile_by_user_id(self, user_id: int) -> dict | None:
        # Trae datos de usuario + persona para poblar la vista de perfil.
        query_with_rol_text = """
            SELECT u.id, u.rol, p.email, p.nombre, p.apellido, p.telefono, p.dni, pa.nombre AS pais
            FROM usuario u
            INNER JOIN persona p ON p.id = u.persona_id
            LEFT JOIN pais pa ON pa.id = p.pais
            WHERE u.id = %s
            LIMIT 1
        """
        query_with_rol_fk = """
            SELECT u.id, r.nombre AS rol, p.email, p.nombre, p.apellido, p.telefono, p.dni, pa.nombre AS pais
            FROM usuario u
            INNER JOIN persona p ON p.id = u.persona_id
            LEFT JOIN rol r ON r.id = u.rol_id
            LEFT JOIN pais pa ON pa.id = p.pais
            WHERE u.id = %s
            LIMIT 1
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                if self._usuario_has_column(cursor, 'rol'):
                    cursor.execute(query_with_rol_text, (user_id,))
                    row = cursor.fetchone()
                else:
                    cursor.execute(query_with_rol_fk, (user_id,))
                    row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "rol": row[1],
            "email": row[2],
            "nombre": row[3],
            "apellido": row[4],
            "telefono": row[5],
            "dni": row[6],
            "pais": row[7],
        }

    def get_password_hash_by_user_id(self, user_id: int) -> str | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT password
                    FROM usuario
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )
                row = cursor.fetchone()

        if not row:
            return None
        return row[0]

    def update_password_by_user_id(self, user_id: int, password_hash: str) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE usuario
                    SET password = %s
                    WHERE id = %s
                    """,
                    (password_hash, user_id),
                )
                updated_rows = cursor.rowcount
            connection.commit()

        return updated_rows > 0
