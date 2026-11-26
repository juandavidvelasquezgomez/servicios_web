import json

import pytest
from sqlalchemy import func, select

from app.models import Medicion
from app.mqtt.ingesta import procesar_mensaje

TOPICO = "iot/sensors/GAS-002/data"


def payload(**cambios) -> dict:
    base = {
        "sensor_id": "GAS-002",
        "timestamp": "2026-10-09T02:53:58Z",
        "measurements": {
            "ch4": {"value": 569.47, "unit": "ppm"},
            "temperature": {"value": 27.69, "unit": "C"},
            "humidity": {"value": 84, "unit": "%"},
        },
    }
    return base | cambios


def con_medida(nombre, **medida) -> dict:
    datos = payload()
    datos["measurements"][nombre] = medida
    return datos


def total(db) -> int:
    return db.scalar(select(func.count()).select_from(Medicion))


def test_mensaje_valido_guarda_un_registro_por_magnitud_con_el_mismo_timestamp(db):
    resultado = procesar_mensaje(db, TOPICO, json.dumps(payload()).encode())

    assert resultado.aceptado
    assert len(resultado.ids) == 3 == total(db)
    assert len(set(db.scalars(select(Medicion.timestamp_utc)))) == 1


@pytest.mark.parametrize(
    ("datos", "motivo"),
    [
        (payload(sensor_id="NO-EXISTE"), "SENSOR_INEXISTENTE"),
        (payload(sensor_id="OFF-001"), "SENSOR_NO_COINCIDE"),
        (con_medida("ch4", value=1, unit="INVALID_UNIT"), "UNIDAD_INCORRECTA"),
        (con_medida("co2", value=400, unit="ppm"), "MAGNITUD_INVALIDA"),
        (con_medida("ch4", value=999999.0, unit="ppm"), "VALOR_FUERA_DE_RANGO"),
        (con_medida("ch4", value="780.24", unit="ppm"), "ESTRUCTURA_O_TIPO_INVALIDO"),
        (con_medida("ch4", value=True, unit="ppm"), "ESTRUCTURA_O_TIPO_INVALIDO"),
        (con_medida("ch4", value=None, unit="ppm"), "ESTRUCTURA_O_TIPO_INVALIDO"),
        (con_medida("ch4", value=float("nan"), unit="ppm"), "ESTRUCTURA_O_TIPO_INVALIDO"),
        (con_medida("ch4", value=1, unit=None), "ESTRUCTURA_O_TIPO_INVALIDO"),
        (con_medida("ch4", value=1), "ESTRUCTURA_O_TIPO_INVALIDO"),
        (payload(measurements={}), "ESTRUCTURA_O_TIPO_INVALIDO"),
        (payload(extra="x"), "ESTRUCTURA_O_TIPO_INVALIDO"),
        ({"sensor_id": "GAS-002"}, "ESTRUCTURA_O_TIPO_INVALIDO"),
        (payload(timestamp="ayer"), "TIMESTAMP_INVALIDO"),
        (payload(timestamp="2026-13-40T25:00:00Z"), "TIMESTAMP_INVALIDO"),
        (payload(timestamp="2026-10-09T02:53:58"), "TIMESTAMP_INVALIDO"),
        (payload(timestamp="2026-10-09T02:53:58-05:00"), "TIMESTAMP_INVALIDO"),
        (payload(timestamp=1760000000), "TIMESTAMP_INVALIDO"),
    ],
)
def test_mensaje_invalido_se_rechaza_completo(db, datos, motivo):
    resultado = procesar_mensaje(db, TOPICO, json.dumps(datos).encode())

    assert (resultado.aceptado, resultado.motivo) == (False, motivo)
    assert total(db) == 0


def test_sensor_inactivo(db):
    datos = payload(sensor_id="OFF-001")
    resultado = procesar_mensaje(db, "iot/sensors/OFF-001/data", json.dumps(datos).encode())

    assert resultado.motivo == "SENSOR_INACTIVO"


@pytest.mark.parametrize(
    "crudo", [b"no es json", b"\xff\xfe", b'{"sensor_id": "A", "sensor_id": "B"}']
)
def test_json_invalido(db, crudo):
    assert procesar_mensaje(db, TOPICO, crudo).motivo == "JSON_INVALIDO"
    assert total(db) == 0
