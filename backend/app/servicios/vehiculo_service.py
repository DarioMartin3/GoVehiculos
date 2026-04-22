import os
import re
import base64
import unicodedata

from app.core.config import DOCS_UPLOAD_DIR
from app.core.database import get_connection
from app.entidades.vehiculo import Vehiculo
from app.adaptadores.document_validator import DocumentValidatorAdapter
from app.repositorios.documento_vehiculo_repository import DocumentoVehiculoRepository
from app.repositorios.usuario_repository import UsuarioRepository
from app.prompts.cedula_vehiculo_prompt import PROMPT_CEDULA_EXTRACCION, PROMPT_CEDULA_TRASERA
from app.prompts.seguro_prompt import PROMPT_SEGURO
from app.repositorios.vehiculo_repository import VehiculoRepository
from app.servicios.token_service import TokenService


def _sanitize_filename_part(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z0-9]", "_", ascii_text.upper().strip())


def _normalize_text(value: str | None) -> str:
    v = (value or "").strip().lower()
    return unicodedata.normalize("NFD", v).encode("ascii", "ignore").decode("ascii")


def _name_tokens(value: str | None) -> set[str]:
    normalized = _normalize_text(value)
    if not normalized:
        return set()
    return set(re.findall(r"[a-z0-9]+", normalized))


def _matches_person_field(extracted_value: str | None, expected_value: str | None) -> bool:
    extracted_norm = _normalize_text(extracted_value)
    expected_norm = _normalize_text(expected_value)

    if not extracted_norm or not expected_norm:
        return False

    if extracted_norm == expected_norm:
        return True

    extracted_tokens = _name_tokens(extracted_norm)
    expected_tokens = _name_tokens(expected_norm)
    if not extracted_tokens or not expected_tokens:
        return False

    return extracted_tokens.issubset(expected_tokens) or expected_tokens.issubset(extracted_tokens)


def _prefer_complete_expected_field(extracted_value: str | None, expected_value: str | None) -> str | None:
    if not _matches_person_field(extracted_value, expected_value):
        return extracted_value

    extracted_tokens = _name_tokens(extracted_value)
    expected_tokens = _name_tokens(expected_value)

    if not expected_tokens:
        return extracted_value

    if extracted_tokens and extracted_tokens.issubset(expected_tokens) and extracted_tokens != expected_tokens:
        return expected_value

    return extracted_value


def _reconcile_person_fields(
    extracted_nombre: str | None,
    extracted_apellido: str | None,
    expected_nombre: str | None,
    expected_apellido: str | None,
) -> tuple[str | None, str | None]:
    nombre = _prefer_complete_expected_field(extracted_nombre, expected_nombre)
    apellido = _prefer_complete_expected_field(extracted_apellido, expected_apellido)

    # Caso frecuente de OCR: coloca "apellido + nombres" en nombre y deja apellido vacío.
    if not _name_tokens(apellido):
        combined_tokens = _name_tokens(nombre)
        expected_name_tokens = _name_tokens(expected_nombre)
        expected_lastname_tokens = _name_tokens(expected_apellido)

        if (
            combined_tokens
            and expected_name_tokens
            and expected_lastname_tokens
            and expected_name_tokens.issubset(combined_tokens)
            and expected_lastname_tokens.issubset(combined_tokens)
        ):
            return expected_nombre, expected_apellido

    # Caso de campos invertidos por OCR.
    if _matches_person_field(nombre, expected_apellido) and _matches_person_field(apellido, expected_nombre):
        return expected_nombre, expected_apellido

    return nombre, apellido


class VehiculoService:
    def __init__(
        self,
        vehiculo_repository: VehiculoRepository | None = None,
        document_validator: DocumentValidatorAdapter | None = None,
    ):
        self.vehiculo_repository = vehiculo_repository or VehiculoRepository()
        self.usuario_repository = UsuarioRepository()
        self.documento_repository = DocumentoVehiculoRepository()
        self.document_validator = document_validator
        self.token_service = TokenService()

    def list_marcas(self) -> list[dict]:
        return self.vehiculo_repository.get_marcas()

    def list_modelos(self, marca_id: int | None = None) -> list[dict]:
        return self.vehiculo_repository.get_modelos(marca_id)

    def _get_request_context(self, token: str) -> tuple[int, str]:
        return self.token_service.get_context(token)

    def _vehicle_to_dict(self, vehicle: Vehiculo) -> dict:
        return vehicle.to_dict()

    def _vehicles_to_dict(self, vehicles: list[Vehiculo]) -> list[dict]:
        return [vehicle.to_dict() for vehicle in vehicles]

    def _validate_vehicle_access(self, role: str, vehicle: Vehiculo, usuario_id: int) -> None:
        if role in {"administrador", "admin", "operador", "soporte"}:
            return

        if role == "socio" and vehicle.usuario_id == usuario_id:
            return

        raise ValueError("Permiso denegado")

    def list_vehicles(self, token: str) -> list[dict]:
        usuario_id, role = self._get_request_context(token)

        if role in {"administrador", "admin", "operador", "soporte"}:
            return self._vehicles_to_dict(self.vehiculo_repository.list_vehicles())

        if role == "socio":
            return self._vehicles_to_dict(self.vehiculo_repository.list_vehicles(usuario_id=usuario_id))

        raise ValueError("Permiso denegado")

    def register_vehicle(self, token: str, patente: str, modelo_id: int, anio: int) -> dict:
        usuario_id, role = self._get_request_context(token)

        if role not in {"cliente", "socio", "administrador", "admin"}:
            raise ValueError("Permiso denegado")

        patente_normalizada = patente.strip().upper()
        if not re.fullmatch(r"[A-Z0-9]{6,10}", patente_normalizada):
            raise ValueError("La patente debe tener entre 6 y 10 caracteres alfanuméricos sin espacios ni símbolos")

        if anio < 1980:
            raise ValueError("El año del vehículo no es válido")

        existing_vehicle = self.vehiculo_repository.get_vehicle_by_patente(patente_normalizada)
        if existing_vehicle:
            raise ValueError("Ya existe un vehículo con esa patente")

        modelo = self.vehiculo_repository.get_modelo_by_id(modelo_id)
        if not modelo:
            raise ValueError("El modelo seleccionado no existe")

        with get_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    vehicle_id = self.vehiculo_repository.create_vehicle(
                        cursor,
                        usuario_id=usuario_id,
                        modelo_id=modelo_id,
                        anio=anio,
                        patente=patente_normalizada,
                    )
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise

        vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("No se pudo registrar el vehículo")

        return self._vehicle_to_dict(vehicle)

    def update_vehicle(self, token: str, vehicle_id: int, data: dict) -> dict:
        usuario_id, role = self._get_request_context(token)

        vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("Vehículo no encontrado")

        self._validate_vehicle_access(role, vehicle, usuario_id)

        payload: dict[str, object] = {}

        if data.get("patente") is not None:
            patente = str(data["patente"]).strip().upper()
            if not re.fullmatch(r"[A-Z0-9]{6,10}", patente):
                raise ValueError("La patente debe tener entre 6 y 10 caracteres alfanuméricos sin espacios ni símbolos")

            existing_vehicle = self.vehiculo_repository.get_vehicle_by_patente(patente)
            if existing_vehicle and existing_vehicle.id != vehicle_id:
                raise ValueError("Ya existe un vehículo con esa patente")

            payload["patente"] = patente

        if data.get("anio") is not None:
            try:
                anio = int(data["anio"])
            except (TypeError, ValueError) as error:
                raise ValueError("El año del vehículo no es válido") from error
            if anio < 1980:
                raise ValueError("El año del vehículo no es válido")
            payload["anio"] = anio

        if data.get("modelo_id") is not None:
            try:
                modelo_id = int(data["modelo_id"])
            except (TypeError, ValueError) as error:
                raise ValueError("El modelo seleccionado no existe") from error

            modelo = self.vehiculo_repository.get_modelo_by_id(modelo_id)
            if not modelo:
                raise ValueError("El modelo seleccionado no existe")
            payload["modelo_id"] = modelo_id

        if not payload:
            raise ValueError("Debe proporcionar al menos un campo para actualizar")

        with get_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    updated = self.vehiculo_repository.update_vehicle_by_id(cursor, vehicle_id, payload)
                    if not updated:
                        raise ValueError("Vehículo no encontrado")
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise

        updated_vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not updated_vehicle:
            raise ValueError("Vehículo no encontrado")

        return self._vehicle_to_dict(updated_vehicle)

    def deactivate_vehicle(self, token: str, vehicle_id: int) -> dict:
        usuario_id, role = self._get_request_context(token)

        vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("Vehículo no encontrado")

        self._validate_vehicle_access(role, vehicle, usuario_id)

        with get_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    updated = self.vehiculo_repository.update_vehicle_status_by_id(cursor, vehicle_id, "Inactivo")
                    if not updated:
                        raise ValueError("Vehículo no encontrado")
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise

        updated_vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not updated_vehicle:
            raise ValueError("Vehículo no encontrado")

        return self._vehicle_to_dict(updated_vehicle)

    def validar_seguro_vehiculo(self, token: str, image_bytes: bytes, marca_esperada: str, modelo_esperado: str) -> dict:
        if not self.document_validator:
            raise ValueError("No hay adaptador de validación configurado")

        usuario_id, _ = self._get_request_context(token)

        perfil = self.usuario_repository.get_profile_by_user_id(usuario_id)
        if not perfil:
            raise ValueError("No se encontraron datos del usuario")

        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        extracted = self.document_validator.extraer_datos(PROMPT_SEGURO, image_b64)

        def _norm_dni(value: str | None) -> str:
            return re.sub(r"[.\s-]", "", (value or "").strip())

        def _norm_date(value: str | None) -> str:
            v = (value or "").strip()
            m = re.match(r"(\d{2})/(\d{2})/(\d{4})", v)
            if m:
                return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
            return v

        def _contains_match(extracted_val: str | None, expected_val: str | None) -> bool:
            a = _normalize_text(extracted_val)
            b = _normalize_text(expected_val)
            return bool(a and b and (b in a or a in b))

        fixed_nombre, fixed_apellido = _reconcile_person_fields(
            extracted.get("nombre"),
            extracted.get("apellido"),
            perfil.get("nombre"),
            perfil.get("apellido"),
        )
        extracted["nombre"] = fixed_nombre
        extracted["apellido"] = fixed_apellido

        coincidencias = {
            "nombre":           _matches_person_field(extracted.get("nombre"), perfil.get("nombre")),
            "apellido":         _matches_person_field(extracted.get("apellido"), perfil.get("apellido")),
            "dni":              _norm_dni(extracted.get("dni"))                == _norm_dni(perfil.get("dni")),
            "fecha_nacimiento": _norm_date(extracted.get("fecha_nacimiento"))  == _norm_date(perfil.get("fecha_nacimiento")),
            "marca":            _contains_match(extracted.get("marca"),  marca_esperada),
            "modelo":           _contains_match(extracted.get("modelo"), modelo_esperado),
        }

        valido = all(coincidencias.values())
        no_coinciden = [k for k, v in coincidencias.items() if not v]

        return {
            "valido": valido,
            "campos_detectados": extracted,
            "coincidencias": coincidencias,
            "mensaje": "Seguro verificado correctamente." if valido
                       else f"No coinciden los campos: {', '.join(no_coinciden)}.",
        }

    def validar_titular_cedula_trasera(self, token: str, image_bytes: bytes) -> dict:
        if not self.document_validator:
            raise ValueError("No hay adaptador de validación configurado")

        usuario_id, _ = self._get_request_context(token)

        perfil = self.usuario_repository.get_profile_by_user_id(usuario_id)
        if not perfil:
            raise ValueError("No se encontraron datos del usuario")

        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        extracted = self.document_validator.extraer_datos(PROMPT_CEDULA_TRASERA, image_b64)

        def _norm_dni(value: str | None) -> str:
            return re.sub(r"[.\s-]", "", (value or "").strip())

        fixed_nombre, fixed_apellido = _reconcile_person_fields(
            extracted.get("nombre"),
            extracted.get("apellido"),
            perfil.get("nombre"),
            perfil.get("apellido"),
        )
        extracted["nombre"] = fixed_nombre
        extracted["apellido"] = fixed_apellido

        coincidencias = {
            "nombre":   _matches_person_field(extracted.get("nombre"), perfil.get("nombre")),
            "apellido": _matches_person_field(extracted.get("apellido"), perfil.get("apellido")),
            "dni":      _norm_dni(extracted.get("dni"))  == _norm_dni(perfil.get("dni")),
        }

        valido = all(coincidencias.values())
        no_coinciden = [k for k, v in coincidencias.items() if not v]

        return {
            "valido": valido,
            "campos_detectados": extracted,
            "coincidencias": coincidencias,
            "mensaje": "Titular verificado correctamente." if valido
                       else f"No coinciden los campos: {', '.join(no_coinciden)}.",
        }

    def extraer_cedula_vehiculo(self, image_bytes: bytes) -> dict:
        if not self.document_validator:
            raise ValueError("No hay adaptador de validación configurado")

        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        extracted = self.document_validator.extraer_datos(PROMPT_CEDULA_EXTRACCION, image_b64)

        marca_nombre = (extracted.get("marca") or "").strip()
        modelo_nombre = (extracted.get("modelo") or "").strip()
        patente = (extracted.get("patente") or "").strip().upper().replace("-", "").replace(" ", "")
        anio = extracted.get("anio")

        if not marca_nombre or not modelo_nombre:
            raise ValueError("No se pudo extraer la marca y modelo de la cédula")

        with get_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    marca_id = self.vehiculo_repository.find_or_create_marca(cursor, marca_nombre)
                    modelo_id = self.vehiculo_repository.find_or_create_modelo(cursor, modelo_nombre, marca_id)
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise

        return {
            "marca": marca_nombre,
            "modelo": modelo_nombre,
            "patente": patente,
            "anio": anio,
            "modelo_id": modelo_id,
        }

    def guardar_documentos_vehiculo(
        self,
        token: str,
        vehicle_id: int,
        archivos: dict[str, tuple[bytes, str] | None],
    ) -> list[dict]:
        usuario_id, role = self._get_request_context(token)

        vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("Vehículo no encontrado")

        if role not in {"administrador", "admin"} and vehicle.usuario_id != usuario_id:
            raise ValueError("Permiso denegado")

        perfil = self.usuario_repository.get_profile_by_user_id(usuario_id)
        nombre_titular = f"{perfil.get('nombre', '')} {perfil.get('apellido', '')}".strip()
        apellido_part = _sanitize_filename_part(perfil.get("apellido") or "")
        nombre_part   = _sanitize_filename_part(perfil.get("nombre")   or "")

        # estado_validacion: 1 = validado, 0 = pendiente
        tipos_config = {
            "cedula_delantera": 1,
            "cedula_trasera":   1,
            "seguro":           1,
            "foto_vehiculo":    0,
        }

        os.makedirs(DOCS_UPLOAD_DIR, exist_ok=True)
        saved: list[dict] = []

        with get_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    for tipo, estado_val in tipos_config.items():
                        archivo = archivos.get(tipo)
                        if not archivo:
                            continue
                        content, ext = archivo
                        if tipo == "foto_vehiculo":
                            n = self.documento_repository.count_by_vehiculo_tipo(cursor, vehicle_id, tipo) + 1
                            filename = f"foto_vehiculo_{apellido_part}_{nombre_part}_{vehicle_id}_{n}.{ext}"
                        else:
                            filename = f"{tipo}_{apellido_part}_{nombre_part}.{ext}"
                        with open(os.path.join(DOCS_UPLOAD_DIR, filename), "wb") as f:
                            f.write(content)
                        doc_id = self.documento_repository.save(
                            cursor, vehicle_id, tipo, nombre_titular, filename, estado_val
                        )
                        saved.append({"id": doc_id, "tipo": tipo, "imagen": filename})
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise

        return saved

    def activate_vehicle(self, token: str, vehicle_id: int) -> dict:
        usuario_id, role = self._get_request_context(token)

        vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("Vehículo no encontrado")

        self._validate_vehicle_access(role, vehicle, usuario_id)

        with get_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    updated = self.vehiculo_repository.update_vehicle_status_by_id(cursor, vehicle_id, "Activo")
                    if not updated:
                        raise ValueError("Vehículo no encontrado")
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise

        updated_vehicle = self.vehiculo_repository.get_vehicle_by_id(vehicle_id)
        if not updated_vehicle:
            raise ValueError("Vehículo no encontrado")

        return self._vehicle_to_dict(updated_vehicle)