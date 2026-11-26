"""Consumidor MQTT: recibe los mensajes del tópico asignado y los entrega a la ingesta."""

import logging
import os

import paho.mqtt.client as mqtt

from app.database.connection import nueva_sesion
from app.mqtt.ingesta import procesar_mensaje

log = logging.getLogger("mqtt")


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code != 0:
        log.error("Error de conexión MQTT: %s", reason_code)
        return
    resultado, _ = client.subscribe(userdata["topico"])
    if resultado != mqtt.MQTT_ERR_SUCCESS:
        log.error("No fue posible suscribirse a %s (código %s)", userdata["topico"], resultado)
        return
    log.info("Conectado y suscrito a %s", userdata["topico"])


def on_disconnect(client, userdata, flags, reason_code, properties=None):
    log.warning("Desconectado del broker: %s", reason_code)


def on_message(client, userdata, message):
    # %r deja el texto externo en una sola línea del registro.
    texto = message.payload[:1000].decode("utf-8", errors="replace")
    log.info("RECIBIDO %s %r", message.topic, texto)
    try:
        with nueva_sesion() as db:
            resultado = procesar_mensaje(db, message.topic, message.payload)
    except Exception:
        # Un fallo (por ejemplo, la base caída) no debe detener el consumidor.
        log.exception("ERROR al procesar el mensaje; no se almacenó")
        return
    if resultado.aceptado:
        log.info("ALMACENADO ids=%s", resultado.ids)
    else:
        log.warning("RECHAZADO %s - %r", resultado.motivo, resultado.detalle)


def iniciar() -> mqtt.Client:
    """Conecta en segundo plano; paho reintenta solo si el broker no responde."""
    broker, topico = os.getenv("MQTT_BROKER"), os.getenv("MQTT_TOPIC")
    if not broker or not topico:
        raise RuntimeError("Faltan MQTT_BROKER y/o MQTT_TOPIC en las variables de entorno")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata={"topico": topico})
    if os.getenv("MQTT_USERNAME"):
        client.username_pw_set(os.environ["MQTT_USERNAME"], os.getenv("MQTT_PASSWORD") or "")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.connect_async(
        broker, int(os.getenv("MQTT_PORT") or 1883), int(os.getenv("MQTT_KEEPALIVE") or 60)
    )
    client.loop_start()
    return client


def detener(client: mqtt.Client) -> None:
    client.disconnect()
    client.loop_stop()
