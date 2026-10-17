"""Consume los eventos de RabbitMQ, los clasifica y manda la alerta al servidor WebSocket."""

import json
import os

import requests

from alertas import EventoInvalido, clasificar_alerta
from conexion import QUEUE_NAME, conectar

WS_BRIDGE_URL = os.environ.get("WS_BRIDGE_URL", "http://localhost:9000/alert")


def enviar_a_ws(alerta):
    """True si el servidor WebSocket recibió la alerta."""
    try:
        respuesta = requests.post(WS_BRIDGE_URL, json=alerta, timeout=2)
        if respuesta.ok:
            return True
        print(f"[Procesador] El servidor WS respondió {respuesta.status_code}: {respuesta.text}", flush=True)
    except requests.RequestException as e:
        print(f"[Procesador] No se pudo enviar al servidor WS: {e}", flush=True)
    return False


def callback(canal, metodo, propiedades, cuerpo):
    try:
        alerta = clasificar_alerta(json.loads(cuerpo))
    except (json.JSONDecodeError, EventoInvalido) as e:
        # Un mensaje mal formado no se puede arreglar reintentando: se descarta.
        print(f"[Procesador] Evento descartado: {e}", flush=True)
        canal.basic_reject(delivery_tag=metodo.delivery_tag, requeue=False)
        return
    print(f"[Procesado] {alerta['nivel']}: {alerta['mensaje']}", flush=True)
    if enviar_a_ws(alerta):
        canal.basic_ack(delivery_tag=metodo.delivery_tag)
    else:
        # Sin servidor WS la alerta vuelve a la cola para no perderla.
        canal.basic_nack(delivery_tag=metodo.delivery_tag, requeue=True)
        canal.connection.sleep(2)


def main():
    conexion, canal = conectar()
    canal.basic_qos(prefetch_count=1)
    canal.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print("[Procesador] Esperando mensajes... Ctrl+C para salir", flush=True)
    try:
        canal.start_consuming()
    except KeyboardInterrupt:
        print("\nSaliendo del procesador...")
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
