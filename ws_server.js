// ws_server.js
const express = require("express");
const http = require("http");
const WebSocket = require("ws");
const os = require("os");

const app = express();
app.use(express.json());

const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

let clients = new Set();

wss.on("connection", (ws) => {
  console.log("[WS Server] Nuevo operador conectado");
  clients.add(ws);

  ws.on("close", () => {
    console.log("[WS Server] Operador desconectado");
    clients.delete(ws);
  });
});

// Endpoint para recibir alertas desde MON Processor
app.post("/alert", (req, res) => {
  const alerta = req.body;
  console.log("[WS Server] Alerta recibida para difundir:", alerta);

  const data = JSON.stringify(alerta);
  for (const client of clients) {
    if (client.readyState === WebSocket.OPEN) {
      client.send(data);
    }
  }

  res.status(200).send("Alert broadcasted");
});

const PORT = 9000;

// Intentar obtener primero la IP del adaptador "Wi-Fi"
function getLocalIp() {
  const nets = os.networkInterfaces();

  // 1) Preferimos el adaptador llamado "Wi-Fi" (así aparece en Windows en español)
  if (nets["Wi-Fi"]) {
    for (const net of nets["Wi-Fi"]) {
      if (net.family === "IPv4" && !net.internal) {
        return net.address; // En tu caso debería ser 10.139.99.40
      }
    }
  }

  // 2) Si no, buscamos cualquier IPv4 válida no interna
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      if (net.family === "IPv4" && !net.internal) {
        return net.address;
      }
    }
  }

  return "localhost";
}

server.listen(PORT, "0.0.0.0", () => {
  const ip = getLocalIp();
  console.log("[WS Server] WebSocket y HTTP escuchando en:");
  console.log(`  ws://localhost:${PORT}`);
  console.log(`  ws://${ip}:${PORT}  (IP para otros equipos de la red)`);
});
