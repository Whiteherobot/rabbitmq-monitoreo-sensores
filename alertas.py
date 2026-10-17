"""Clasificación de los eventos de sensores en alertas verde, amarilla o roja."""

# Umbrales de los sensores numéricos: (amarillo desde, rojo desde, unidad, nombre, texto en rojo)
UMBRALES = {
    "temperatura": (35, 45, "°C", "Temperatura", "posible sobrecalentamiento"),
    "humo": (20, 60, "%", "Humo", "posible incendio"),
    "vibracion": (3, 7, "g", "Vibración", "posible daño estructural"),
}

# Estados de los sensores binarios: valor -> (nivel, alerta)
ESTADOS = {
    "puerta": {"abierta": ("amarillo", "Puerta abierta"), "cerrada": ("verde", "Puerta cerrada")},
    "movimiento": {"detectado": ("amarillo", "Movimiento detectado"), "no_detectado": ("verde", "Sin movimiento")},
    "alarma_manual": {"activada": ("rojo", "Alarma manual activada"), "inactiva": ("verde", "Alarma manual inactiva")},
}


class EventoInvalido(ValueError):
    pass


def clasificar_alerta(evento):
    """Devuelve la alerta (nivel, título y mensaje) junto con los datos del evento."""
    tipo = evento.get("tipo")
    valor = evento.get("valor")
    sensor = evento.get("sensor_id")
    lugar = evento.get("ubicacion")
    donde = f"{sensor} ({lugar})" if lugar else str(sensor)

    if tipo in UMBRALES:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise EventoInvalido(f"{tipo} necesita un valor numérico, llegó {valor!r}")
        amarillo, rojo, unidad, nombre, riesgo = UMBRALES[tipo]
        if valor >= rojo:
            nivel, alerta = "rojo", f"{nombre} crítica" if tipo != "humo" else "Humo crítico"
            mensaje = f"{donde}: {valor} {unidad}, {riesgo}."
        elif valor >= amarillo:
            nivel, alerta = "amarillo", f"{nombre} elevada" if tipo != "humo" else "Humo elevado"
            mensaje = f"{donde}: {valor} {unidad}, supera {amarillo} {unidad}; revisar."
        else:
            nivel, alerta = "verde", f"{nombre} normal"
            mensaje = f"{donde}: {valor} {unidad}."
    elif tipo in ESTADOS:
        if valor not in ESTADOS[tipo]:
            raise EventoInvalido(f"{tipo} no tiene el estado {valor!r}")
        nivel, alerta = ESTADOS[tipo][valor]
        mensaje = f"{alerta} en {donde}."
    else:
        raise EventoInvalido(f"tipo de sensor desconocido: {tipo!r}")

    return {
        "alerta": alerta,
        "nivel": nivel,
        "mensaje": mensaje,
        "sensor_id": sensor,
        "ubicacion": lugar,
        "tipo": tipo,
        "valor": valor,
        "timestamp": evento.get("timestamp"),
    }
