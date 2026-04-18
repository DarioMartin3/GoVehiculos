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
