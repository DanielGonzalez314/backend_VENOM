import uvicorn
import os
import sys
from pathlib import Path

# --- 1. CONFIGURACIÓN DE RUTAS DEL SISTEMA ---
# Forzamos que la raíz del proyecto esté en el path para evitar errores de importación
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

# Importaciones internas
from app.database import engine, Base
from app.api.endpoints import router as api_router
from app.core.logging_config import setup_logging

# Inicializar configuración de logs
setup_logging()

app = FastAPI(
    title="Venom Intelligence API",
    description="Core Backend con Soporte de Vision, Tools y RAG",
    version="2.1.0",
    docs_url="/docs" if os.getenv("ENV") != "production" else None
)

# --- 2. CONFIGURACIÓN DE CORS ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Company-ID"] 
)

# --- 3. MANEJO GLOBAL DE EXCEPCIONES ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Logueo detallado en consola para depuración
    logger.error(f"🚨 CRITICAL: {request.method} {request.url.path} | Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": f"Venom Engine Error: {str(exc)}"
        },
    )

# --- 4. MIDDLEWARE DE TRAZABILIDAD ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    company_id = request.headers.get("X-Company-ID", "anonymous")
    with logger.contextualize(company_id=company_id):
        logger.info(f"IN: {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            logger.info(f"OUT: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"FLOW ERROR: {str(e)}")
            raise e

# --- 5. DEFINICIÓN DE RUTAS ---
app.include_router(api_router, prefix="/api")

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "active", 
        "engine": "Venom 2.1.0",
        "timestamp": "2026-05-04"
    }

# --- 6. EVENTO DE ARRANQUE (STARTUP) ---
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando servicios de Venom...")
    try:
        # Crea las tablas automáticamente si no existen
        # Importante: Si cambiaste nombres en models.py, recuerda limpiar el esquema public antes
        Base.metadata.create_all(bind=engine)
        logger.success("🧬 PostgreSQL: Tablas sincronizadas correctamente.")
    except Exception as e:
        logger.critical(f"❌ Error de conexión a la base de datos: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)