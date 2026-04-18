from contextlib import contextmanager

import psycopg2

from app.core.config import DATABASE_HOST, DATABASE_NAME, DATABASE_PASSWORD, DATABASE_PORT, DATABASE_USER


@contextmanager
def get_connection():
    """Abre una conexión a PostgreSQL y la cierra automáticamente al salir del bloque `with`."""
    connection = psycopg2.connect(
        host=DATABASE_HOST,
        port=DATABASE_PORT,
        dbname=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
    )
    try:
        yield connection
    finally:
        connection.close()
