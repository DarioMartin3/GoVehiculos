from fastapi import APIRouter, Header, HTTPException, UploadFile, File, status

from app.servicios.licencia_service import LicenciaService

router = APIRouter(prefix="/licencias", tags=["licencias"])


@router.post("/validate")
async def validate_licencia(
    documento: UploadFile = File(...),
    authorization: str | None = Header(default=None),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if documento.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato no soportado. Usá JPG, PNG o WEBP.")

    imagen_bytes = await documento.read()
    if len(imagen_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen no puede superar los 5MB.")

    try:
        result = LicenciaService().validar_y_guardar(token, imagen_bytes)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        print(f"[validate-licencia ERROR] {type(error).__name__}: {error}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudo conectar con el servicio de validación.") from error

    return result


@router.get("/me")
def get_mi_licencia(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        return LicenciaService().obtener_licencia(token)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
