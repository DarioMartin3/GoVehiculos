from app.adaptadores.groq_adapter import GroqDocumentAdapter
from app.core.database import get_connection
from app.repositorios.licencia_repository import LicenciaRepository
from app.repositorios.usuario_repository import UsuarioRepository
from app.servicios.licencia_validation_service import LicenciaValidationService
from app.servicios.token_service import TokenService


class LicenciaService:
    def __init__(self):
        self.token_service = TokenService()
        self.usuario_repository = UsuarioRepository()
        self.licencia_repository = LicenciaRepository()
        self.validation_service = LicenciaValidationService(adapter=GroqDocumentAdapter(max_tokens=1024))

    def validar_y_guardar(self, token: str, image_bytes: bytes) -> dict:
        user_id = self.token_service.validate_token(token)

        persona = self.usuario_repository.get_persona_basica_by_user_id(user_id)
        if not persona:
            raise ValueError("Usuario no encontrado")

        result = self.validation_service.validate(
            image_bytes=image_bytes,
            nombre=persona["nombre"],
            apellido=persona["apellido"],
            fecha_nacimiento=persona["fecha_nacimiento"] or "",
        )

        if result["valido"]:
            datos = result["datos_extraidos"]
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    try:
                        self.licencia_repository.crear_carnet(
                            cursor,
                            usuario_id=user_id,
                            fecha_emision=datos.get("fecha_emision"),
                            fecha_vencimiento=datos.get("fecha_vencimiento"),
                            clases=datos.get("clases", []),
                        )
                        connection.commit()
                    except Exception:
                        connection.rollback()
                        raise

        return result

    def obtener_licencia(self, token: str) -> dict:
        user_id = self.token_service.validate_token(token)

        carnet = self.licencia_repository.get_carnet_by_usuario(user_id)
        if not carnet:
            raise ValueError("No se encontró licencia registrada")

        return carnet
