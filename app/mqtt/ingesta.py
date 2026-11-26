"""Validación de un mensaje MQTT y almacenamiento de sus mediciones."""

import json
from dataclasses import dataclass, field
from decimal import Decimal

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sensor_magnitud
from app.models import Medicion
from app.schemas.medicion import MensajePayload


class Rechazo(Exception):
    """El mensaje no supera una validación; no se almacena nada."""

    def __init__(self, motivo: str, detalle: str):
        super().__init__(f"{motivo}: {detalle}")
        self.motivo = motivo
        self.detalle = detalle


@dataclass
class Resultado:
    aceptado: bool
    motivo: str = ""
    detalle: str = ""
    ids: list[int] = field(default_factory=list)


def _sin_claves_repetidas(pares: list[tuple[str, object]]) -> dict:
    objeto = dict(pares)
    if len(objeto) != len(pares):
        raise ValueError("el JSON tiene claves repetidas")
    return objeto


def validar_estructura(crudo: bytes) -> MensajePayload:
    """Decodifica el JSON y valida estructura, tipos y timestamp con Pydantic."""
    try:
        datos = json.loads(crudo.decode("utf-8"), object_pairs_hook=_sin_claves_repetidas)
    except (ValueError, RecursionError) as error:
        raise Rechazo("JSON_INVALIDO", str(error)) from error
    try:
        return MensajePayload.model_validate(datos)
    except ValidationError as error:
        errores = error.errors()
        detalle = "; ".join(
            f"{'.'.join(map(str, e['loc'])) or 'mensaje'}: {e['msg']}" for e in errores
        )
        if all(e["loc"][:1] == ("timestamp",) and e["type"] != "missing" for e in errores):
            raise Rechazo("TIMESTAMP_INVALIDO", detalle) from error
        raise Rechazo("ESTRUCTURA_O_TIPO_INVALIDO", detalle) from error


def sensor_del_topico(topico: str) -> str | None:
    partes = topico.split("/")
    if len(partes) == 4 and partes[:2] == ["iot", "sensors"] and partes[3] == "data":
        return partes[2]
    return None


def validar_contra_catalogo(db: Session, mensaje: MensajePayload, topico: str) -> list[Medicion]:
    """Valida sensor, estado, magnitudes, unidades y rangos; arma los registros a guardar."""
    sensor = crud_sensor.obtener_por_codigo(db, mensaje.sensor_id)
    if sensor is None:
        raise Rechazo("SENSOR_INEXISTENTE", f"no existe el sensor '{mensaje.sensor_id}'")
    esperado = sensor_del_topico(topico)
    if esperado is not None and esperado != sensor.codigo:
        raise Rechazo(
            "SENSOR_NO_COINCIDE", f"'{sensor.codigo}' publicado en el tópico de '{esperado}'"
        )
    if not sensor.activo:
        raise Rechazo("SENSOR_INACTIVO", f"el sensor '{sensor.codigo}' está inactivo")

    # Solo magnitudes de este sensor: así la clave foránea siempre es consistente.
    catalogo = {m.magnitud: m for m in crud_sensor_magnitud.listar_por_sensor(db, sensor.id)}
    registros = []
    for nombre, medida in mensaje.measurements.items():
        configurada = catalogo.get(nombre)
        if configurada is None:
            raise Rechazo(
                "MAGNITUD_INVALIDA", f"'{nombre}' no pertenece al sensor '{sensor.codigo}'"
            )
        if medida.unit != configurada.unidad:
            raise Rechazo(
                "UNIDAD_INCORRECTA",
                f"{nombre}: se recibió '{medida.unit}' y se esperaba '{configurada.unidad}'",
            )
        valor = Decimal(str(medida.value))
        minimo, maximo = configurada.valor_minimo, configurada.valor_maximo
        if not minimo <= valor <= maximo:
            raise Rechazo(
                "VALOR_FUERA_DE_RANGO", f"{nombre}: {valor} no está entre {minimo} y {maximo}"
            )
        registros.append(
            Medicion(
                sensor_magnitud_id=configurada.id, valor=valor, timestamp_utc=mensaje.timestamp
            )
        )
    return registros


def procesar_mensaje(db: Session, topico: str, crudo: bytes) -> Resultado:
    """Almacena el mensaje solo si todas sus magnitudes son válidas."""
    try:
        mensaje = validar_estructura(crudo)
        registros = validar_contra_catalogo(db, mensaje, topico)
    except Rechazo as rechazo:
        return Resultado(False, rechazo.motivo, rechazo.detalle)
    guardados = crud_medicion.crear_lote(db, registros)
    return Resultado(True, ids=[m.id for m in guardados])
