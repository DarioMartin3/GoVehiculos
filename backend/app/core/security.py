from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import os

from jose import JWTError, jwt

from app.core.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET_KEY

# Prefijo y costo para guardar contraseñas con PBKDF2.
PBKDF2_PREFIX = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 260000


def _pbkdf2_hash(password: str, salt: bytes) -> bytes:
    # Deriva un hash seguro combinando contraseña + salt + iteraciones.
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)


def verify_password(plain_password: str, stored_password: str) -> bool:
    """Valida una contraseña contra su valor almacenado en la base."""
    if stored_password.startswith(f"{PBKDF2_PREFIX}$"):
        parts = stored_password.split("$")
        if len(parts) != 4:
            return False
        _, iterations, salt_b64, hash_b64 = parts
        try:
            iterations_int = int(iterations)
            salt = base64.b64decode(salt_b64.encode("ascii"))
            expected = base64.b64decode(hash_b64.encode("ascii"))
            computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations_int)
            return hmac.compare_digest(computed, expected)
        except (ValueError, TypeError):
            return False

    # Compatibilidad con contraseñas antiguas en texto plano.
    return plain_password == stored_password


def hash_password(password: str) -> str:
    """Genera un hash seguro para guardar contraseñas nuevas."""
    salt = os.urandom(16)
    password_hash = _pbkdf2_hash(password, salt)
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(password_hash).decode("ascii")
    return f"{PBKDF2_PREFIX}${PBKDF2_ITERATIONS}${salt_b64}${hash_b64}"


def create_access_token(subject: str, extra_claims: dict | None = None) -> str:
    """Crea un token JWT con expiración para la sesión del usuario."""
    payload = {"sub": subject, "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decodifica y valida un JWT de acceso."""
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as error:
        raise ValueError("Token inválido") from error
