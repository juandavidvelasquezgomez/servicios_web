import json

from app.mqtt.ingesta import procesar_mensaje
from scripts.generar_evidencias import base_de_datos

TOPICO = "iot/sensors/GAS-002/data"


def test_comprobacion_en_base_de_datos(db):
    valido = {
        "sensor_id": "GAS-002",
        "timestamp": "2026-10-09T02:00:00Z",
        "measurements": {"ch4": {"value": 100, "unit": "ppm"}},
    }
    invalido = valido | {
        "timestamp": "2026-10-09T02:00:05Z",
        "measurements": {"ch4": {"value": 100, "unit": "X"}},
    }
    assert procesar_mensaje(db, TOPICO, json.dumps(valido).encode()).aceptado
    lineas = [
        f"2026-10-09 02:00:05,000 INFO RECIBIDO {TOPICO} {json.dumps(invalido)!r}",
        "2026-10-09 02:00:05,001 WARNING RECHAZADO UNIDAD_INCORRECTA - 'x'",
    ]

    informe = base_de_datos(db, lineas, "GAS-002")

    assert "Mediciones almacenadas: 1" in informe
    assert "| 4. Unidad incorrecta | 2026-10-09T02:00:05+00:00 | 0 |" in informe
