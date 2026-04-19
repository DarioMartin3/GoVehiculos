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

    def _get_estado_id(self, cursor, estado: str) -> int:
        cursor.execute(
            """
            SELECT id
            FROM estado
            WHERE LOWER(nombre) = LOWER(%s)
            LIMIT 1
            """,
            (estado,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("El estado enviado no existe en la base de datos")
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

    def update_persona_by_user_id(self, user_id: int, email: str | None, telefono: str | None, pais: int | None) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT persona_id
                    FROM usuario
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return False

                persona_id = row[0]

                updates = []
                values = []

                if email is not None:
                    updates.append("email = %s")
                    values.append(email)
                if telefono is not None:
                    updates.append("telefono = %s")
                    values.append(telefono)
                if pais is not None:
                    updates.append("pais = %s")
                    values.append(pais)

                if not updates:
                    return True

                values.append(persona_id)
                update_clause = ", ".join(updates)
                cursor.execute(
                    f"""
                    UPDATE persona
                    SET {update_clause}
                    WHERE id = %s
                    """,
                    tuple(values),
                )
                updated_rows = cursor.rowcount
            connection.commit()

        return updated_rows > 0

    def get_users_directory(self) -> list[dict]:
        query_with_rol_text = """
            SELECT u.id, p.email, u.rol, u.estado, p.nombre, p.apellido, p.telefono, pa.nombre AS pais
            FROM usuario u
            INNER JOIN persona p ON p.id = u.persona_id
            LEFT JOIN pais pa ON pa.id = p.pais
            ORDER BY p.apellido ASC, p.nombre ASC
        """
        query_with_rol_fk = """
            SELECT u.id, p.email, r.nombre AS rol, u.estado, p.nombre, p.apellido, p.telefono, pa.nombre AS pais
            FROM usuario u
            INNER JOIN persona p ON p.id = u.persona_id
            LEFT JOIN rol r ON r.id = u.rol_id
            LEFT JOIN pais pa ON pa.id = p.pais
            ORDER BY p.apellido ASC, p.nombre ASC
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                if self._usuario_has_column(cursor, 'rol'):
                    cursor.execute(query_with_rol_text)
                else:
                    cursor.execute(query_with_rol_fk)
                rows = cursor.fetchall()

        users = []
        for row in rows:
            users.append({
                'id': row[0],
                'email': row[1],
                'rol': row[2],
                'estado': row[3],
                'nombre': row[4],
                'apellido': row[5],
                'telefono': row[6],
                'pais': row[7],
            })
        return users

    def get_user_directory_item_by_id(self, user_id: int) -> dict | None:
        query_with_rol_text = """
            SELECT u.id, p.email, u.rol, u.estado, p.nombre, p.apellido, p.telefono, pa.nombre AS pais
            FROM usuario u
            INNER JOIN persona p ON p.id = u.persona_id
            LEFT JOIN pais pa ON pa.id = p.pais
            WHERE u.id = %s
            LIMIT 1
        """
        query_with_rol_fk = """
            SELECT u.id, p.email, r.nombre AS rol, u.estado, p.nombre, p.apellido, p.telefono, pa.nombre AS pais
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
                else:
                    cursor.execute(query_with_rol_fk, (user_id,))
                row = cursor.fetchone()

        if not row:
            return None

        return {
            'id': row[0],
            'email': row[1],
            'rol': row[2],
            'estado': row[3],
            'nombre': row[4],
            'apellido': row[5],
            'telefono': row[6],
            'pais': row[7],
        }

    def update_user_directory_by_id(self, user_id: int, data: dict) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT persona_id
                    FROM usuario
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (user_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return False

                persona_id = row[0]
                persona_updates = []
                persona_values = []
                usuario_updates = []
                usuario_values = []

                if data.get('email') is not None:
                    persona_updates.append('email = %s')
                    persona_values.append(data['email'])
                if data.get('nombre') is not None:
                    persona_updates.append('nombre = %s')
                    persona_values.append(data['nombre'])
                if data.get('apellido') is not None:
                    persona_updates.append('apellido = %s')
                    persona_values.append(data['apellido'])
                if data.get('telefono') is not None:
                    persona_updates.append('telefono = %s')
                    persona_values.append(data['telefono'])
                if data.get('pais') is not None:
                    persona_updates.append('pais = %s')
                    persona_values.append(data['pais'])

                if data.get('estado') is not None:
                    usuario_updates.append('estado = %s')
                    usuario_values.append(data['estado'])

                if data.get('rol') is not None:
                    if self._usuario_has_column(cursor, 'rol'):
                        usuario_updates.append('rol = %s')
                        usuario_values.append(data['rol'])
                    else:
                        rol_id = self._get_rol_id(cursor, data['rol'])
                        usuario_updates.append('rol_id = %s')
                        usuario_values.append(rol_id)

                if persona_updates:
                    persona_values.append(persona_id)
                    cursor.execute(
                        f"""
                        UPDATE persona
                        SET {', '.join(persona_updates)}
                        WHERE id = %s
                        """,
                        tuple(persona_values),
                    )

                if usuario_updates:
                    usuario_values.append(user_id)
                    cursor.execute(
                        f"""
                        UPDATE usuario
                        SET {', '.join(usuario_updates)}
                        WHERE id = %s
                        """,
                        tuple(usuario_values),
                    )

            connection.commit()

        return True

    def deactivate_user_by_id(self, user_id: int) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                estado_inactivo_id = self._get_estado_id(cursor, 'Inactivo')
                cursor.execute(
                    """
                    UPDATE usuario
                    SET estado = %s
                    WHERE id = %s
                    """,
                    (estado_inactivo_id, user_id),
                )
                updated_rows = cursor.rowcount
            connection.commit()

        return updated_rows > 0

    def activate_user_by_id(self, user_id: int) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                estado_activo_id = self._get_estado_id(cursor, 'Activo')
                cursor.execute(
                    """
                    UPDATE usuario
                    SET estado = %s
                    WHERE id = %s
                    """,
                    (estado_activo_id, user_id),
                )
                updated_rows = cursor.rowcount
            connection.commit()

        return updated_rows > 0
