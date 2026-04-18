from app.entidades import Persona


class PersonaRepository:
    def create(self, cursor, persona: Persona) -> int:
        # Inserta persona y devuelve el id recién creado (RETURNING id).
        cursor.execute(
            """
            INSERT INTO persona (nombre, apellido, email, telefono, dni, pais)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                persona.nombre,
                persona.apellido,
                persona.email,
                persona.telefono,
                persona.dni,
                persona.pais,
            ),
        )
        return cursor.fetchone()[0]
