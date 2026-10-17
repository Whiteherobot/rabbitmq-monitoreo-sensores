"""Publica en RabbitMQ las lecturas de los sensores simulados."""

import json
import os
import random
import time

import pika

from conexion import QUEUE_NAME, conectar
from sensores import Simulador

INTERVALO = (float(os.environ.get("INTERVALO_MIN", 0.5)), float(os.environ.get("INTERVALO_MAX", 3.0)))


def main():
    conexion, canal = conectar()
    simulador = Simulador()
    print("[Productor] Enviando eventos de sensores... Ctrl+C para salir", flush=True)
    try:
        while True:
            cuerpo = json.dumps(simulador.siguiente_evento(), ensure_ascii=False)
            canal.basic_publish(
                exchange="",
                routing_key=QUEUE_NAME,
                body=cuerpo,
                properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
            )
            print(f"[Enviado] {cuerpo}", flush=True)
            time.sleep(random.uniform(*INTERVALO))
    except KeyboardInterrupt:
        print("\nSaliendo del productor...")
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
