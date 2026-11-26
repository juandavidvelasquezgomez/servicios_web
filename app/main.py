"""Punto de entrada: `uvicorn app.main:app` inicia la API y el consumidor MQTT."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.api import medicion, sensor, sensor_magnitud
from app.mqtt import client as mqtt_client

load_dotenv()


def configurar_registro() -> None:
    archivo = Path(os.getenv("LOG_FILE") or "logs/mqtt.log")
    archivo.parent.mkdir(parents=True, exist_ok=True)
    formato = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    registro = logging.getLogger("mqtt")
    registro.setLevel(logging.INFO)
    registro.handlers.clear()
    for manejador in (logging.StreamHandler(), logging.FileHandler(archivo, encoding="utf-8")):
        manejador.setFormatter(formato)
        registro.addHandler(manejador)


@asynccontextmanager
async def lifespan(app: FastAPI):
    consumidor = None
    if os.getenv("MQTT_ENABLED", "true").lower() == "true":
        configurar_registro()
        consumidor = mqtt_client.iniciar()
    yield
    if consumidor is not None:
        mqtt_client.detener(consumidor)


app = FastAPI(title="API de mediciones IoT", version="1.0.0", lifespan=lifespan)
app.include_router(sensor.router)
app.include_router(sensor_magnitud.router)
app.include_router(medicion.router)


@app.exception_handler(OperationalError)
def base_de_datos_no_disponible(request: Request, error: OperationalError):
    logging.getLogger("uvicorn.error").error("Base de datos no disponible: %s", error)
    return JSONResponse({"detail": "Base de datos no disponible"}, status_code=503)
