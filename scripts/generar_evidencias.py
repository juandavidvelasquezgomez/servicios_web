"""Genera evidencias a partir de la API en ejecución y del registro MQTT.

Uso (con `uvicorn app.main:app` corriendo):
    python scripts/generar_evidencias.py --codigo GAS-002

Escribe `evidencias/consultas_http.md` y `evidencias/mensajes_mqtt.md` solo con
respuestas y líneas de registro reales; lo que no aparezca queda marcado como pendiente.
"""

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

MAXIMO_ELEMENTOS = 5
MOTIVOS = {
    "3. Sensor inexistente": "RECHAZADO SENSOR_INEXISTENTE",
    "4. Unidad incorrecta": "RECHAZADO UNIDAD_INCORRECTA",
    "5. Tipo de dato incorrecto": "RECHAZADO ESTRUCTURA_O_TIPO_INVALIDO",
    "6. Magnitud incorrecta": "RECHAZADO MAGNITUD_INVALIDA",
    "7. Timestamp inválido": "RECHAZADO TIMESTAMP_INVALIDO",
    "Adicional: valor fuera de rango": "RECHAZADO VALOR_FUERA_DE_RANGO",
    "Adicional: JSON inválido": "RECHAZADO JSON_INVALIDO",
}


def consultas_http(api: httpx.Client, codigo: str) -> str:
    sensor = api.get(f"/sensores/por-codigo/{codigo}").raise_for_status().json()
    base = f"/sensores/{sensor['id']}"
    ultima = api.get(f"{base}/ultima-medicion").raise_for_status().json()
    magnitud = ultima["magnitud"]
    # Ventana de 10 minutos que termina en la última medición (hora de Colombia).
    fin = datetime.strptime(ultima["fecha_hora_colombia"][:19], "%Y-%m-%d %H:%M:%S")
    desde = (fin - timedelta(minutes=10)).isoformat()
    hasta = fin.isoformat()

    pruebas = [
        ("8. Consulta por ID existente", f"/mediciones/{ultima['id']}", 200),
        ("9. Consulta por ID inexistente", "/mediciones/999999999999", 404),
        ("10. Consulta histórica", f"{base}/mediciones", 200),
        ("11. Rango de fechas", f"{base}/mediciones?desde={desde}&hasta={hasta}", 200),
        ("12. Rango desde > hasta", f"{base}/mediciones?desde={hasta}&hasta={desde}", 400),
        ("13. Validación HTTP incorrecta", f"{base}/mediciones?limit=0", 422),
        ("14. Última medición", f"{base}/ultima-medicion", 200),
        ("15. Últimas N mediciones", f"{base}/mediciones?limit=5", 200),
        ("16. Filtro por magnitud", f"{base}/mediciones?magnitud={magnitud}&limit=5", 200),
        (
            "Adicional: filtros combinados",
            f"{base}/mediciones?magnitud={magnitud}&desde={desde}&hasta={hasta}&limit=5",
            200,
        ),
        ("17. Claves foráneas: sensor", f"{base}", 200),
        ("17. Claves foráneas: magnitudes", f"{base}/magnitudes", 200),
        (
            "17. Claves foráneas: magnitud de la medición",
            f"/sensor-magnitudes/{ultima['sensor_magnitud_id']}",
            200,
        ),
    ]

    partes = [encabezado("Consultas HTTP")]
    for titulo, ruta, esperado in pruebas:
        respuesta = api.get(ruta)
        cuerpo = respuesta.json()
        nota = ""
        if isinstance(cuerpo, list) and len(cuerpo) > MAXIMO_ELEMENTOS:
            nota = f"Se muestran {MAXIMO_ELEMENTOS} de {len(cuerpo)} elementos.\n\n"
            cuerpo = cuerpo[:MAXIMO_ELEMENTOS]
        estado = "cumple" if respuesta.status_code == esperado else f"NO cumple ({esperado})"
        partes.append(
            f"## {titulo}\n\n- Solicitud: `GET {ruta}`\n"
            f"- Código HTTP: `{respuesta.status_code}` ({estado})\n\n{nota}"
            f"```json\n{json.dumps(cuerpo, indent=2, ensure_ascii=False)}\n```\n"
        )
    return "\n".join(partes)


def mensajes_mqtt(registro: Path) -> str:
    lineas = registro.read_text(encoding="utf-8").splitlines() if registro.exists() else []
    partes = [encabezado("Mensajes MQTT"), resumen(lineas)]
    casos = {"1. Recepción MQTT": " RECIBIDO ", "2. Medición válida": " ALMACENADO "} | MOTIVOS
    for titulo, marca in casos.items():
        indice = next((i for i, linea in enumerate(lineas) if marca in linea), None)
        if indice is None:
            partes.append(f"## {titulo}\n\nPendiente: aún no aparece en el registro.\n")
            continue
        # El mensaje que originó un resultado es el RECIBIDO inmediatamente anterior.
        previo = next(
            (linea for linea in reversed(lineas[:indice]) if " RECIBIDO " in linea), None
        )
        bloque = [lineas[indice]] if marca == " RECIBIDO " or previo is None else [previo, lineas[indice]]
        partes.append(f"## {titulo}\n\n```text\n" + "\n".join(bloque) + "\n```\n")
    return "\n".join(partes)


def resumen(lineas: list[str]) -> str:
    recibidos = [linea for linea in lineas if " RECIBIDO " in linea]
    almacenados = sum(" ALMACENADO " in linea for linea in lineas)
    rechazados = sum(bool(re.search(r" RECHAZADO ", linea)) for linea in lineas)
    texto = f"- Mensajes recibidos: {len(recibidos)}\n- Almacenados: {almacenados}\n"
    texto += f"- Rechazados: {rechazados}\n"
    if recibidos:
        # Cada línea empieza con la fecha local del equipo: "AAAA-MM-DD HH:MM:SS,mmm".
        inicio, fin = (datetime.strptime(l[:19], "%Y-%m-%d %H:%M:%S") for l in (recibidos[0], recibidos[-1]))
        minutos = (fin - inicio).total_seconds() / 60
        texto += f"- Primer a último mensaje: {inicio} a {fin} ({minutos:.1f} minutos)\n"
    return texto


def encabezado(titulo: str) -> str:
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return f"# {titulo}\n\nGenerado por `scripts/generar_evidencias.py` el {ahora}.\n"


def main() -> None:
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--url", default="http://127.0.0.1:8000")
    argumentos.add_argument("--codigo", default="GAS-002")
    argumentos.add_argument("--registro", type=Path, default=Path("logs/mqtt.log"))
    argumentos.add_argument("--salida", type=Path, default=Path("evidencias"))
    opciones = argumentos.parse_args()

    opciones.salida.mkdir(parents=True, exist_ok=True)
    (opciones.salida / "mensajes_mqtt.md").write_text(
        mensajes_mqtt(opciones.registro), encoding="utf-8"
    )
    with httpx.Client(base_url=opciones.url, timeout=30) as api:
        (opciones.salida / "consultas_http.md").write_text(
            consultas_http(api, opciones.codigo), encoding="utf-8"
        )
    print(f"Evidencias generadas en {opciones.salida}/")


if __name__ == "__main__":
    main()
