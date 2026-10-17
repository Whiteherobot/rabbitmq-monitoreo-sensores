// Recibe las alertas del procesador por HTTP y las difunde por WebSocket a los
// operadores conectados. También sirve la pantalla del operador (public/).
const express = require("express");
const http = require("http");
const os = require("os");
const path = require("path");
const WebSocket = require("ws");

const NIVELES = ["verde", "amarillo", "rojo"];
const HISTORIAL = 50;

function crearServidor() {
  const app = express();
  app.use(express.json());
  app.use(express.static(path.join(__dirname, "public")));

  const server = http.createServer(app);
  const wss = new WebSocket.Server({ server });
  const historial = []; // las últimas alertas, la más nueva al final

  wss.on("connection", (ws) => {
    console.log("[WS] Operador conectado");
    // Quien se conecta tarde recibe lo último que pasó.
    ws.send(JSON.stringify({ tipo: "historial", alertas: historial }));
    ws.on("close", () => console.log("[WS] Operador desconectado"));
  });

  app.post("/alert", (req, res) => {
    const alerta = req.body;
    if (!alerta || !NIVELES.includes(alerta.nivel) || !alerta.sensor_id || !alerta.mensaje) {
      return res.status(400).json({ error: "La alerta necesita sensor_id, mensaje y un nivel verde, amarillo o rojo." });
    }
    historial.push(alerta);
    if (historial.length > HISTORIAL) historial.shift();

    const datos = JSON.stringify({ tipo: "alerta", alerta });
    let enviados = 0;
    for (const cliente of wss.clients) {
      if (cliente.readyState === WebSocket.OPEN) {
        cliente.send(datos);
        enviados++;
      }
    }
    res.json({ difundida: true, operadores: enviados });
  });

  app.get("/alerts", (req, res) => res.json(historial));
  app.get("/health", (req, res) => res.json({ status: "ok", operadores: wss.clients.size }));

  return { app, server, wss };
}

/** Primera IPv4 externa, para avisar desde qué dirección pueden conectarse otros equipos. */
function ipLocal() {
  for (const interfaces of Object.values(os.networkInterfaces())) {
    for (const red of interfaces ?? []) {
      if (red.family === "IPv4" && !red.internal) return red.address;
    }
  }
  return "localhost";
}

if (require.main === module) {
  const PORT = Number(process.env.PORT || 9000);
  const { server } = crearServidor();
  server.listen(PORT, "0.0.0.0", () => {
    console.log(`[WS] Pantalla del operador: http://localhost:${PORT}`);
    console.log(`[WS] Desde otros equipos de la red: http://${ipLocal()}:${PORT}`);
  });
  process.on("SIGTERM", () => server.close(() => process.exit(0)));
}

module.exports = { crearServidor };
