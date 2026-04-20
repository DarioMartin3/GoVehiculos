from app.servicios.document_validation_service import DocumentValidationService
from app.adaptadores.groq_adapter import GroqDocumentAdapter
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/validate-document")
async def validate_document(
    documento: UploadFile = File(...),
    nombre: str = Form(...),
    apellido: str = Form(...),
    dni: str = Form(...),
    fecha_nacimiento: str = Form(...),
):
    

    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if documento.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato no soportado. Usá JPG, PNG o WEBP.")

    imagen_bytes = await documento.read()
    if len(imagen_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen no puede superar los 5MB.")


    try:
        service = DocumentValidationService(adapter=GroqDocumentAdapter())

        result = service.validate(
            image_bytes=imagen_bytes,
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            fecha_nacimiento=fecha_nacimiento,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        print(f"[validate-document ERROR] {type(error).__name__}: {error}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudo conectar con el servicio de validación.") from error

    return result
