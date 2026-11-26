import json

import pytest

from app.mqtt.ingesta import procesar_mensaje


@pytest.fixture
def datos(db):
    """Tres mensajes válidos (02:00, 02:05 y 02:10 UTC) con dos magnitudes cada uno."""
    for minuto, ch4 in ((0, 100), (5, 200), (10, 300)):
        mensaje = {
            "sensor_id": "GAS-002",
            "timestamp": f"2026-10-09T02:{minuto:02}:00Z",
            "measurements": {
                "ch4": {"value": ch4, "unit": "ppm"},
                "temperature": {"value": 25.5, "unit": "C"},
            },
        }
        crudo = json.dumps(mensaje).encode()
        assert procesar_mensaje(db, "iot/sensors/GAS-002/data", crudo).aceptado


@pytest.mark.parametrize(
    "ruta",
    [
        "/sensores",
        "/sensores/1",
        "/sensores/por-codigo/GAS-002",
        "/sensores/1/magnitudes",
        "/sensor-magnitudes/1",
        "/mediciones/1",
        "/sensores/1/mediciones",
        "/sensores/1/ultima-medicion",
    ],
)
def test_rutas_responden_200(api, datos, ruta):
    assert api.get(ruta).status_code == 200


@pytest.mark.parametrize(
    "ruta",
    [
        "/sensores/999",
        "/sensores/por-codigo/NADA",
        "/sensores/999/magnitudes",
        "/sensor-magnitudes/999",
        "/mediciones/999",
        "/sensores/999/mediciones",
        "/sensores/999/ultima-medicion",
        "/sensores/2/ultima-medicion",
    ],
)
def test_inexistente_responde_404(api, datos, ruta):
    assert api.get(ruta).status_code == 404


@pytest.mark.parametrize(
    "ruta",
    [
        "/sensores/abc",
        "/sensores/99999999999",
        "/mediciones/0",
        "/sensores/1/mediciones?limit=0",
        "/sensores/1/mediciones?desde=ayer",
    ],
)
def test_validacion_http_responde_422(api, ruta):
    assert api.get(ruta).status_code == 422


def test_rango_invertido_responde_400(api):
    respuesta = api.get(
        "/sensores/1/mediciones?desde=2026-10-09T10:00:00Z&hasta=2026-10-09T09:00:00Z"
    )

    assert respuesta.status_code == 400


def test_respuesta_en_hora_de_colombia(api, datos):
    ultima = api.get("/sensores/1/ultima-medicion?magnitud=ch4").json()

    assert ultima["fecha_hora_colombia"] == "2026-10-08 21:10:00 -05:00"
    assert (ultima["valor"], ultima["unidad"]) == (300, "ppm")


def test_filtros_combinados(api, datos):
    # Sin zona horaria, desde/hasta son hora de Colombia: 21:05 = 02:05 UTC.
    parametros = {
        "magnitud": "ch4",
        "desde": "2026-10-08T21:00:00",
        "hasta": "2026-10-08T21:05:00",
    }
    respuesta = api.get("/sensores/1/mediciones", params=parametros).json()

    assert [m["valor"] for m in respuesta] == [200, 100]


def test_limit_devuelve_las_ultimas(api, datos):
    respuesta = api.get("/sensores/1/mediciones?magnitud=ch4&limit=2").json()

    assert [m["valor"] for m in respuesta] == [300, 200]


def test_filtro_utc(api, datos):
    respuesta = api.get("/sensores/1/mediciones?desde=2026-10-09T02:10:00Z").json()

    assert len(respuesta) == 2
