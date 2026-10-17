"""Conexión a RabbitMQ con reintentos (al levantar todo junto, el broker tarda en aceptar conexiones)."""

import os
import time

import pika

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
QUEUE_NAME = os.environ.get("QUEUE_NAME", "sensores_mon")


def conectar(intentos=30, espera=2.0):
    for intento in range(1, intentos + 1):
        try:
            conexion = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            canal = conexion.channel()
            canal.queue_declare(queue=QUEUE_NAME, durable=True)
            return conexion, canal
        except pika.exceptions.AMQPConnectionError:
            print(f"RabbitMQ en {RABBITMQ_HOST} no responde (intento {intento}/{intentos})", flush=True)
            time.sleep(espera)
    raise SystemExit(f"No se pudo conectar a RabbitMQ en {RABBITMQ_HOST}")
