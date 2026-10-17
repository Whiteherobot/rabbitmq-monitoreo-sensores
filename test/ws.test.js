const { test, beforeEach, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const WebSocket = require("ws");
const { crearServidor } = require("../ws_server");

let servidor, base;
const alerta = (nivel = "rojo", sensor_id = "S-101") => ({
  alerta: "Temperatura crítica", nivel, mensaje: "S-101 (Sala de servidores): 47 °C.", sensor_id, tipo: "temperatura", valor: 47,
});

beforeEach(async () => {
  servidor = crearServidor().server.listen(0);
  await new Promise((r) => servidor.once("listening", r));
  base = `127.0.0.1:${servidor.address().port}`;
});
afterEach(() => new Promise((r) => { servidor.closeAllConnections?.(); servidor.close(r); }));

const enviar = (cuerpo) =>
  fetch(`http://${base}/alert`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) });

/** Abre un operador y junta los mensajes que recibe. */
async function operador() {
  const ws = new WebSocket(`ws://${base}`);
  const mensajes = [];
  ws.on("message", (m) => mensajes.push(JSON.parse(m)));
  await new Promise((r) => ws.once("open", r));
  await new Promise((r) => setTimeout(r, 30));
  return { ws, mensajes };
}

test("difunde la alerta a todos los operadores conectados", async () => {
  const a = await operador();
  const b = await operador();
  const res = await enviar(alerta());
  assert.deepEqual(await res.json(), { difundida: true, operadores: 2 });
  await new Promise((r) => setTimeout(r, 50));
  for (const o of [a, b]) {
    assert.equal(o.mensajes.at(-1).tipo, "alerta");
    assert.equal(o.mensajes.at(-1).alerta.nivel, "rojo");
    o.ws.close();
  }
});

test("quien se conecta tarde recibe el historial", async () => {
  await enviar(alerta("verde", "S-105"));
  await enviar(alerta("amarillo", "S-106"));
  const o = await operador();
  assert.equal(o.mensajes[0].tipo, "historial");
  assert.deepEqual(o.mensajes[0].alertas.map((x) => x.sensor_id), ["S-105", "S-106"]);
  o.ws.close();
});

test("rechaza alertas incompletas y guarda solo las últimas 50", async () => {
  assert.equal((await enviar({ nivel: "morado", sensor_id: "S-1", mensaje: "x" })).status, 400);
  assert.equal((await enviar({ nivel: "rojo" })).status, 400);
  for (let i = 0; i < 55; i++) await enviar(alerta("verde", `S-${i}`));
  const historial = await (await fetch(`http://${base}/alerts`)).json();
  assert.equal(historial.length, 50);
  assert.equal(historial[0].sensor_id, "S-5");
});

test("sirve la pantalla del operador", async () => {
  const html = await (await fetch(`http://${base}/`)).text();
  assert.match(html, /Monitoreo de sensores/);
  assert.equal((await fetch(`http://${base}/health`)).status, 200);
});
