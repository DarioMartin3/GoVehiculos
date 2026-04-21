from app.core.security import create_access_token, decode_access_token

class TokenService:
    def validate_token(self, token: str) -> int:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")
        try:
            user_id = int(user_id_raw)
        except (TypeError, ValueError):
            raise ValueError("Token inválido")
        return user_id

    def get_role(self, token: str) -> str:
        payload = decode_access_token(token)
        return (payload.get("rol") or "").strip().lower()

    def create_token(self, user_id: int, email: str, rol: str) -> str:
        return create_access_token(
            subject=str(user_id),
            extra_claims={"email": email, "rol": rol},
        )

    def get_context(self, token: str) -> tuple[int, str]:
        payload = decode_access_token(token)
        try:
            user_id = int(payload.get("sub"))
        except (TypeError, ValueError):
            raise ValueError("Token inválido")
        role = (payload.get("rol") or "").strip().lower()
        return user_id, role