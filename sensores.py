"""Sensores simulados de un edificio.

Cada sensor tiene un tipo y una ubicación fijos, y su lectura cambia poco a
poco (una caminata aleatoria) en lugar de saltar al azar en cada evento, como
pasaría con un sensor real.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Sensor:
    id: str
    tipo: str
    ubicacion: str
    valor: object = field(default=None)


# tipo: (mínimo, máximo, paso máximo por lectura, valor inicial)
RANGOS = {
    "temperatura": (15.0, 70.0, 1.5, 24.0),  # °C
    "humo": (0.0, 100.0, 4.0, 5.0),          # % de oscurecimiento
    "vibracion": (0.0, 10.0, 0.6, 0.5),      # g
}

# tipo: (estados posibles, probabilidad de cambiar en cada lectura, estado inicial)
BINARIOS = {
    "puerta": (("cerrada", "abierta"), 0.15, "cerrada"),
    "movimiento": (("no_detectado", "detectado"), 0.25, "no_detectado"),
    "alarma_manual": (("inactiva", "activada"), 0.02, "inactiva"),
}

CATALOGO = [
    Sensor("S-101", "temperatura", "Sala de servidores"),
    Sensor("S-102", "temperatura", "Cocina"),
    Sensor("S-103", "humo", "Cocina"),
    Sensor("S-104", "humo", "Bodega"),
    Sensor("S-105", "puerta", "Entrada principal"),
    Sensor("S-106", "puerta", "Bodega"),
    Sensor("S-107", "movimiento", "Pasillo norte"),
    Sensor("S-108", "vibracion", "Cuarto de máquinas"),
    Sensor("S-109", "alarma_manual", "Recepción"),
]


class Simulador:
    def __init__(self, sensores=None, rng=None):
        self.rng = rng or random.Random()
        self.sensores = [Sensor(s.id, s.tipo, s.ubicacion) for s in (sensores or CATALOGO)]
        for s in self.sensores:
            s.valor = RANGOS[s.tipo][3] if s.tipo in RANGOS else BINARIOS[s.tipo][2]

    def leer(self, sensor):
        """Actualiza la lectura del sensor y la devuelve."""
        if sensor.tipo in RANGOS:
            minimo, maximo, paso, _ = RANGOS[sensor.tipo]
            sensor.valor = round(min(maximo, max(minimo, sensor.valor + self.rng.uniform(-paso, paso))), 1)
        else:
            estados, cambio, _ = BINARIOS[sensor.tipo]
            if self.rng.random() < cambio:
                sensor.valor = estados[1] if sensor.valor == estados[0] else estados[0]
        return sensor.valor

    def siguiente_evento(self, ahora=None):
        sensor = self.rng.choice(self.sensores)
        return {
            "sensor_id": sensor.id,
            "tipo": sensor.tipo,
            "ubicacion": sensor.ubicacion,
            "valor": self.leer(sensor),
            "timestamp": (ahora or datetime.now(timezone.utc)).isoformat(),
        }
