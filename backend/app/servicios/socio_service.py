from app.core.security import create_access_token, decode_access_token
from app.repositorios.usuario_repository import UsuarioRepository
from app.repositorios.vehiculo_repository import VehiculoRepository


class SocioService:
    def __init__(
        self,
        vehiculo_repository: VehiculoRepository | None = None,
        usuario_repository: UsuarioRepository | None = None,
    ):
        self.vehiculo_repository = vehiculo_repository or VehiculoRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()

    def promover_a_socio_si_aplica(self, token: str) -> str | None:
        """
        Si el usuario es cliente y acaba de registrar su primer vehículo,
        lo promueve a socio y devuelve un nuevo token con el rol actualizado.
        Devuelve None si no aplica la promoción.
        """
        try:
            payload = decode_access_token(token)
            usuario_id = int(payload.get("sub"))
            rol_actual = (payload.get("rol") or "").strip().lower()
        except Exception:
            return None

        if rol_actual != "cliente":
            return None

        vehiculos = self.vehiculo_repository.list_vehicles(usuario_id=usuario_id)
        if len(vehiculos) != 1:
            return None

        self.usuario_repository.update_rol_by_user_id(usuario_id, "Socio")

        perfil = self.usuario_repository.get_profile_by_user_id(usuario_id)
        email = (perfil or {}).get("email", "")

        return create_access_token(
            subject=str(usuario_id),
            extra_claims={"email": email, "rol": "Socio"},
        )
