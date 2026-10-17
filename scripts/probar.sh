#!/usr/bin/env bash
# Prueba de punta a punta: con el compose levantado, las alertas tienen que
# llegar del productor, pasar por RabbitMQ y el procesador, y salir por el
# servidor WebSocket.
#   scripts/probar.sh [http://localhost:9000]
set -uo pipefail
ws="${1:-http://localhost:9000}"

for _ in $(seq 60); do
  n=$(curl -s "$ws/alerts" | grep -o '"sensor_id"' | wc -l)
  if (( n >= 5 )); then
    echo "ok     llegaron $n alertas al servidor WebSocket"
    curl -s "$ws/" | grep -q "Monitoreo de sensores" && echo "ok     pantalla del operador" || { echo "FALLA  pantalla"; exit 1; }
    exit 0
  fi
  sleep 2
done
echo "FALLA  no llegaron alertas en 2 minutos"
exit 1
