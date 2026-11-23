from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import os
import logging
import time
import random

app = FastAPI(
    title="Gaia Backend API - The Cosmic Grill",
    description="API Positrónica de procesamiento para Terminus",
    version="1.0.0"
)

# Configuración del registro (Logging) para que Agatha pueda oler el humo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

### Obtenemos las variables de entorno inyectadas por Kubernetes
DB_USER = os.getenv("DB_USER", "sysadmin")
DB_PASS = os.getenv("DB_PASS", "positronic_password")
DB_HOST = os.getenv("DB_HOST", "gaia-db-service")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "terminus_data")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

### Configuración del motor de base de datos
engine = create_engine(DATABASE_URL)

@app.get("/")
def read_root():
    return {"message": "Bienvenido al Nodo Positrónico - Backend Operativo (The Cosmic Grill)"}

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

# --- NUEVO ENDPOINT PARA "THE COSMIC GRILL" ---
@app.get("/pedir")
def procesar_pedido(item: str):
    """
    Simula el procesamiento de una comanda en la cocina positrónica.
    Añade un retraso artificial (latencia) para que Locust pueda ahogar la capacidad del pod.
    """
    logging.info(f"🍔 Cocina recibiendo comanda: {item}")

    # Simulamos el tiempo que tarda la cocinera (Gaia) en preparar el pedido
    # Esto es crucial para el Chaos Engineering: si Locust lanza 200 peticiones
    # por segundo y cada una tarda medio segundo, el pod se asfixiará rápido.
    time.sleep(random.uniform(0.1, 0.5))

    # En un escenario más avanzado, aquí podríamos consultar la DB (Términus)
    # para descontar inventario de la Hamburguesa o Malteada.

    return {"status": "success", "message": f"{item.capitalize()} en preparación en The Cosmic Grill."}
