import random
from datetime import datetime, timezone

import pytest

from alertas import EventoInvalido, clasificar_alerta
from sensores import CATALOGO, Simulador


def evento(tipo, valor, ubicacion="Cocina"):
    return {"sensor_id": "S-1", "tipo": tipo, "valor": valor, "ubicacion": ubicacion, "timestamp": "t"}


@pytest.mark.parametrize(
    "tipo,valor,nivel",
    [
        ("temperatura", 34.9, "verde"), ("temperatura", 35, "amarillo"), ("temperatura", 45, "rojo"),
        ("humo", 19.9, "verde"), ("humo", 20, "amarillo"), ("humo", 60, "rojo"),
        ("vibracion", 2.9, "verde"), ("vibracion", 7, "rojo"),
        ("puerta", "abierta", "amarillo"), ("movimiento", "no_detectado", "verde"),
        ("alarma_manual", "activada", "rojo"),
    ],
)
def test_niveles_en_los_limites(tipo, valor, nivel):
    assert clasificar_alerta(evento(tipo, valor))["nivel"] == nivel


def test_el_mensaje_dice_donde_y_cuanto():
    alerta = clasificar_alerta(evento("temperatura", 47.2, "Sala de servidores"))
    assert alerta["alerta"] == "Temperatura crítica"
    assert alerta["mensaje"] == "S-1 (Sala de servidores): 47.2 °C, posible sobrecalentamiento."
    assert alerta["timestamp"] == "t"


@pytest.mark.parametrize("ev", [evento("temperatura", "caliente"), evento("puerta", "rota"), evento("radar", 1), {}])
def test_eventos_invalidos(ev):
    with pytest.raises(EventoInvalido):
        clasificar_alerta(ev)


def test_el_simulador_cambia_de_a_poco_y_respeta_los_rangos():
    sim = Simulador(rng=random.Random(1))
    servidores = next(s for s in sim.sensores if s.id == "S-101")
    lecturas = [sim.leer(servidores) for _ in range(500)]
    assert all(15 <= v <= 70 for v in lecturas)
    assert max(abs(b - a) for a, b in zip(lecturas, lecturas[1:])) <= 1.6


def test_cada_sensor_mantiene_su_tipo_y_ubicacion():
    sim = Simulador(rng=random.Random(2))
    tipos = {s.id: (s.tipo, s.ubicacion) for s in CATALOGO}
    ahora = datetime(2026, 10, 17, tzinfo=timezone.utc)
    for _ in range(200):
        ev = sim.siguiente_evento(ahora)
        assert (ev["tipo"], ev["ubicacion"]) == tipos[ev["sensor_id"]]
        assert ev["timestamp"] == "2026-10-17T00:00:00+00:00"
        clasificar_alerta(ev)  # todo evento simulado se puede clasificar
