from app.core.security import decode_access_token

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