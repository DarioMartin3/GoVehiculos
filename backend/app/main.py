from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.presentacion.auth_router import router as auth_router
from app.presentacion.vehiculo_router import router as vehiculo_router
from app.presentacion.auth_documents import router as documents_router
from app.presentacion.licencia_router import router as licencia_router

# Punto de entrada principal del backend.
app = FastAPI()

# CORS habilita llamadas desde el frontend (puerto 3000) al backend (puerto 8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta rutas de autenticación con prefijo /auth.
app.include_router(auth_router)
app.include_router(vehiculo_router)
app.include_router(documents_router)
app.include_router(licencia_router)


@app.get("/")
def root():
    # Endpoint de prueba para validar que la API está arriba.
    return {"msg": "ok"}