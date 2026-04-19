from fastapi import APIRouter, Header, HTTPException, status

from app.schemas import VehicleBrandResponse, VehicleCreateRequest, VehicleModelResponse, VehicleResponse, VehicleUpdateRequest
from app.servicios.vehiculo_service import VehiculoService

router = APIRouter(prefix="/vehiculos", tags=["vehiculos"])


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


@router.post("", response_model=VehicleResponse)
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

    return VehicleResponse(**result)


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