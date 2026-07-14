from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import os

app = FastAPI(
    title="Gaia Backend API",
    description="API Positrónica de procesamiento para Terminus",
    version="1.0.0"
)

# Obtenemos las variables de entorno inyectadas por Kubernetes
DB_USER = os.getenv("DB_USER", "sysadmin")
DB_PASS = os.getenv("DB_PASS", "positronic_password")
DB_HOST = os.getenv("DB_HOST", "gaia-db-service")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "terminus_data")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configuración del motor de base de datos
engine = create_engine(DATABASE_URL)

@app.get("/")
def read_root():
    return {"message": "Bienvenido al Nodo Positrónico - Backend Operativo"}

@app.get("/health")
def health_check():
    """Endpoint ligero para que los Precogs y K8s validen que el pod está vivo."""
    return {"status": "ok", "service": "gaia-backend"}

@app.get("/status/db")
def db_status():
    """Valida la conexión real con Términus (PostgreSQL)."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            db_version = result.scalar()
            return {"status": "conectado", "terminus_version": db_version}
    except OperationalError as e:
        raise HTTPException(status_code=503, detail="Error al conectar con Términus")
