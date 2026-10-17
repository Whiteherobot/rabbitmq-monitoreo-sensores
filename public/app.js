// Pantalla del operador: se conecta por WebSocket al mismo servidor que la sirve.
const MAXIMO = 100;
const nombresNivel = { verde: "Normal", amarillo: "Advertencia", rojo: "Crítico" };
const conteo = { verde: 0, amarillo: 0, rojo: 0 };
const sensores = new Map();

const $ = (id) => document.getElementById(id);

function hora(iso) {
  const fecha = new Date(iso);
  return Number.isNaN(fecha.getTime()) ? "" : fecha.toLocaleTimeString("es-EC");
}

function lectura(a) {
  const unidades = { temperatura: " °C", humo: " %", vibracion: " g" };
  return typeof a.valor === "number" ? `${a.valor}${unidades[a.tipo] ?? ""}` : String(a.valor).replace("_", " ");
}

function agregar(alerta) {
  conteo[alerta.nivel]++;
  for (const nivel of Object.keys(conteo)) $(`n-${nivel}`).textContent = conteo[nivel];

  const li = document.createElement("li");
  li.className = alerta.nivel;
  const texto = document.createElement("span");
  texto.className = "texto";
  texto.textContent = `${alerta.alerta}: ${alerta.mensaje}`;
  const detalle = document.createElement("small");
  detalle.textContent = `${nombresNivel[alerta.nivel]} · ${hora(alerta.timestamp)}`;
  li.append(texto, detalle);
  $("alertas").prepend(li);
  while ($("alertas").children.length > MAXIMO) $("alertas").lastChild.remove();

  sensores.set(alerta.sensor_id, alerta);
  dibujarSensores();
}

function dibujarSensores() {
  const filas = [...sensores.values()].sort((a, b) => a.sensor_id.localeCompare(b.sensor_id));
  $("sensores").replaceChildren(
    ...filas.map((a) => {
      const tr = document.createElement("tr");
      for (const [texto, clase] of [
        [a.sensor_id],
        [a.ubicacion ?? ""],
        [lectura(a)],
        [nombresNivel[a.nivel], `estado ${a.nivel}`],
      ]) {
        const td = document.createElement("td");
        td.textContent = texto;
        if (clase) td.className = clase;
        tr.append(td);
      }
      return tr;
    }),
  );
}

function conectar() {
  const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`);
  ws.onopen = () => {
    $("conexion").textContent = "Conectado";
    $("conexion").className = "conexion activa";
  };
  ws.onmessage = (e) => {
    const mensaje = JSON.parse(e.data);
    if (mensaje.tipo === "historial") mensaje.alertas.forEach(agregar);
    else if (mensaje.tipo === "alerta") agregar(mensaje.alerta);
  };
  ws.onclose = () => {
    $("conexion").textContent = "Sin conexión, reintentando...";
    $("conexion").className = "conexion caida";
    setTimeout(conectar, 2000);
  };
}

$("solo-importantes").addEventListener("change", (e) => document.body.classList.toggle("ocultar-normales", e.target.checked));
conectar();
