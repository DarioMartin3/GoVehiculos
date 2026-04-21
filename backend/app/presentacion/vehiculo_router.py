from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile, status

from app.adaptadores.groq_adapter import GroqDocumentAdapter
from app.schemas import CedulaTitularValidacionResponse, CedulaVehiculoExtractResponse, DocumentoVehiculoResponse, SeguroValidacionResponse, VehicleBrandResponse, VehicleCreateRequest, VehicleModelResponse, VehicleRegisterResponse, VehicleResponse, VehicleUpdateRequest
from app.servicios.socio_service import SocioService
from app.servicios.vehiculo_service import VehiculoService

router = APIRouter(prefix="/vehiculos", tags=["vehiculos"])


@router.post("/seguro/validar", response_model=SeguroValidacionResponse)
async def validar_seguro(
    seguro: UploadFile = File(...),
    marca: str = Form(...),
    modelo: str = Form(...),
    authorization: str | None = Header(default=None),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if seguro.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato no soportado. Usá JPG, PNG o WEBP.")

    image_bytes = await seguro.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen no puede superar los 10MB.")

    try:
        result = VehiculoService(document_validator=GroqDocumentAdapter()).validar_seguro_vehiculo(
            token, image_bytes, marca, modelo
        )
    except ValueError as error:
        message = str(error)
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error
    except Exception as error:
        print(f"[validar-seguro ERROR] {type(error).__name__}: {error}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudo conectar con el servicio de validación.") from error

    return SeguroValidacionResponse(**result)


@router.post("/cedula/validar-titular", response_model=CedulaTitularValidacionResponse)
async def validar_titular_cedula(
    cedula: UploadFile = File(...),
    authorization: str | None = Header(default=None),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if cedula.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato no soportado. Usá JPG, PNG o WEBP.")

    image_bytes = await cedula.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen no puede superar los 10MB.")

    try:
        result = VehiculoService(document_validator=GroqDocumentAdapter()).validar_titular_cedula_trasera(token, image_bytes)
    except ValueError as error:
        message = str(error)
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error
    except Exception as error:
        print(f"[validar-titular ERROR] {type(error).__name__}: {error}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudo conectar con el servicio de validación.") from error

    return CedulaTitularValidacionResponse(**result)


@router.post("/cedula/extraer", response_model=CedulaVehiculoExtractResponse)
async def extraer_cedula_vehiculo(cedula: UploadFile = File(...)):
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if cedula.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato no soportado. Usá JPG, PNG o WEBP.")

    image_bytes = await cedula.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen no puede superar los 10MB.")

    try:
        result = VehiculoService(document_validator=GroqDocumentAdapter()).extraer_cedula_vehiculo(image_bytes)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        print(f"[extraer-cedula ERROR] {type(error).__name__}: {error}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudo conectar con el servicio de extracción.") from error

    return CedulaVehiculoExtractResponse(**result)


@router.get("/marcas", response_model=list[VehicleBrandResponse])
def list_brands():
    return [VehicleBrandResponse(**item) for item in VehiculoService().list_marcas()]


@router.get("/modelos", response_model=list[VehicleModelResponse])
def list_models(marca_id: int | None = None):
    return [VehicleModelResponse(**item) for item in VehiculoService().list_modelos(marca_id)]


@router.get("", response_model=list[VehicleResponse])
def list_vehicles(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        result = VehiculoService().list_vehicles(token)
    except ValueError as error:
        message = str(error)
        if message == "Permiso denegado":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from error
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error

    return [VehicleResponse(**item) for item in result]


@router.post("/{vehicle_id}/documentos", response_model=list[DocumentoVehiculoResponse])
async def guardar_documentos_vehiculo(
    vehicle_id: int,
    cedula_delantera: UploadFile | None = File(default=None),
    cedula_trasera: UploadFile | None = File(default=None),
    seguro: UploadFile | None = File(default=None),
    foto_vehiculo: UploadFile | None = File(default=None),
    authorization: str | None = Header(default=None),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}

    async def _read(upload: UploadFile | None) -> tuple[bytes, str] | None:
        if not upload or not upload.filename:
            return None
        if upload.content_type not in allowed_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Formato no soportado en {upload.filename}. Usá JPG, PNG o WEBP.")
        content = await upload.read()
        ext = upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else "jpg"
        return content, ext

    archivos = {
        "cedula_delantera": await _read(cedula_delantera),
        "cedula_trasera":   await _read(cedula_trasera),
        "seguro":           await _read(seguro),
        "foto_vehiculo":    await _read(foto_vehiculo),
    }

    try:
        result = VehiculoService().guardar_documentos_vehiculo(token, vehicle_id, archivos)
    except ValueError as error:
        message = str(error)
        if message in {"Token inválido", }:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        if message == "Permiso denegado":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from error
        if message == "Vehículo no encontrado":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error
    except Exception as error:
        print(f"[guardar-documentos ERROR] {type(error).__name__}: {error}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudieron guardar los documentos.") from error

    return [DocumentoVehiculoResponse(**d) for d in result]


@router.post("", response_model=VehicleRegisterResponse)
def register_vehicle(payload: VehicleCreateRequest, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        result = VehiculoService().register_vehicle(token, payload.patente, payload.modelo_id, payload.anio)
    except ValueError as error:
        message = str(error)
        if message == "Permiso denegado":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from error
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error

    nuevo_token = SocioService().promover_a_socio_si_aplica(token)
    return VehicleRegisterResponse(**result, nuevo_token=nuevo_token)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: int, payload: VehicleUpdateRequest, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        result = VehiculoService().update_vehicle(token, vehicle_id, payload.model_dump(exclude_unset=True))
    except ValueError as error:
        message = str(error)
        if message == "Permiso denegado":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from error
        if message == "Vehículo no encontrado":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from error
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error

    return VehicleResponse(**result)


@router.delete("/{vehicle_id}", response_model=VehicleResponse)
def deactivate_vehicle(vehicle_id: int, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        result = VehiculoService().deactivate_vehicle(token, vehicle_id)
    except ValueError as error:
        message = str(error)
        if message == "Permiso denegado":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from error
        if message == "Vehículo no encontrado":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from error
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error

    return VehicleResponse(**result)


@router.post("/{vehicle_id}/activate", response_model=VehicleResponse)
def activate_vehicle(vehicle_id: int, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        result = VehiculoService().activate_vehicle(token, vehicle_id)
    except ValueError as error:
        message = str(error)
        if message == "Permiso denegado":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from error
        if message == "Vehículo no encontrado":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from error
        if message == "Token inválido":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message) from error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from error

    return VehicleResponse(**result)