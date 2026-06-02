from flask import Flask, render_template_string, url_for
import os

app = Flask(__name__)

# LOCAL
# BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5001")
# CON DOCKER COMPOSE
# BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:5001")
# PARA INGRESS K8S
BACKEND_URL = os.getenv("BACKEND_URL")
if not BACKEND_URL:
    raise RuntimeError("BACKEND_URL no configurado")

TEMPLATE = """
<!doctype html>
<html lang="es" data-theme="light">
<head>
  <meta charset="utf-8">
  <title>Simulación de carga digital en IMV</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='favicon.ico') }}">

  <style>
    :root {
      --bg-light: #f5f5f5;
      --bg-dark: #1e1e1e;
      --text-light: #222;
      --text-dark: #eee;
      --card-light: #fff;
      --card-dark: #2a2a2a;
    }
    [data-theme="light"] { --bg: var(--bg-light); --text: var(--text-light); --card: var(--card-light); }
    [data-theme="dark"] { --bg: var(--bg-dark); --text: var(--text-dark); --card: var(--card-dark); }

    body { margin: 0; font-family: Arial; background: var(--bg); color: var(--text); }
    header { display: flex; align-items: center; justify-content: space-between; padding: 1rem; background: #b30000; color: white; }
    header img { height: 40px; margin-right: 10px; }
    .title { display: flex; align-items: center; font-size: 1.2rem; font-weight: bold; }
    nav { display: none; flex-direction: column; background: #8a0000; padding: 1rem; }
    nav a { color: white; text-decoration: none; margin: 0.5rem 0; }
    .hamburger { cursor: pointer; font-size: 1.5rem; }
    @media (min-width: 700px) { nav { display: flex !important; flex-direction: row; background: none; } nav a { margin: 0 1rem; } .hamburger { display: none; } }
    .container { padding: 1rem; }
    table { width: 100%; border-collapse: collapse; background: var(--card); }
    th, td { padding: 0.5rem; border: 1px solid #ccc; }
    th { background: #724fc9; color: var(--bg-light);}
    .triage-rojo { color: red; font-weight: bold; }
    .triage-amarillo { color: #c7a600; font-weight: bold; }
    .triage-verde { color: green; font-weight: bold; }
    .toggle-theme { cursor: pointer; background: white; color: black; padding: 0.3rem 0.6rem; border-radius: 5px; }
    pre { background: #111; color: #eee; padding: 0.5rem; overflow-x: auto; max-height: 200px; }
    #sim-table tbody tr { color: #111 !important; } 
    #sim-table tbody tr td { color: #111 !important; }

    .pagination { margin-top: 1rem; display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
    .pagination input { width: 60px; }
  </style>
</head>

<body>

<header>
  <div class="title">
    <img src="{{logo_url}}">
    Simulación de carga digital en IMV
  </div>
  <div class="hamburger" onclick="toggleMenu()">☰</div>
  <nav id="menu">
    <a href="#simulaciones">Simulaciones</a>
    <a href="#pacientes">Pacientes</a>
    <span class="toggle-theme" onclick="toggleTheme()">🌓</span>
  </nav>
</header>

<div class="container" id="simulaciones">
  <h2>Simulaciones de carga</h2>

  <form onsubmit="startSimulation(event)">
    <label>Escenario de simulación:</label>
    <select id="scenario">
      <option value="escenario_1">Escenario 1 - Explosion</option>
      <option value="escenario_2">Escenario 2 - Avalancha</option>
      <option value="escenario_3">Escenario 3 - Otra</option>
      <option value="escenario_4">Escenario 4 - Stress</option>
    </select>

    <button id="btn-simular" type="submit">Iniciar simulación</button>
    <!-- Loader oculto por defecto -->
    <span id="sim-loader" style="display:none; margin-left:10px; font-size:1.4rem;">⏳</span>  
    <button id="btn-stop" type="button"
            onclick="stopSimulation()"
            style="display:none; margin-left:10px; background:#ff4d4d; color:white;">
      ⛔ Parar simulación
    </button>      
  </form>

  <div id="sim-result" style="margin-top:10px;"></div>

  <div id="sim-history-container" style="display:none; margin-top:20px;">

    <div class="historial" style="display:flex; justify-content:space-between; align-items:center; width:100%; margin-top:10px;">
      <h3 style="margin-top:20px;">Historial de simulaciones</h3>

      <!-- Botón de refresco estilo tabla de historial -->
      <button onclick="loadSimulations()" style="font-size:1.2rem; float:right;">🔄</button>
    </div>
    <table id="sim-table" style="margin-top:-10px;">
      <thead>
        <tr>
          <th>Fecha-Hora</th>
          <th>Escenario</th>
          <th>Duración (s)</th>
          <th>Latencia media (ms)</th>
          <th>VUs</th>
          <th>Throughput (req/s)</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</div>
<div class="container" id="pacientes">
  <h2>Pacientes recibidos</h2>

  <div class="pagination" style="display:flex; justify-content:space-between; align-items:center; width:100%; margin-top:10px;">

    <!-- Controles de paginación -->
    <div style="display:flex; gap:0.5rem; align-items:center;">
      <button onclick="goFirst()">⏮</button>
      <button onclick="goPrev()">◀</button>

      Página <span id="page-number">1</span> de <span id="total-pages">1</span>

      <button onclick="goNext()">▶</button>
      <button onclick="goLast()">⏭</button>

      | Ir a página:
      <input id="goto-page" type="number" min="1" style="width:60px;">
      <button onclick="goToPage()">Ir</button>
    </div>

    <!-- Botón de recarga con icono -->
    <button onclick="reloadPatients()" style="font-size:1.2rem;" name="Recargar">🔄</button>

  </div>


  <table id="patients-table">
    <thead>
      <tr>
        <th>ID</th>
        <th>Dispositivo</th>
        <th>Seq</th>
        <th>Edad</th>
        <th>Género</th>
        <th>Lesión</th>
        <th>Triage</th>
        <th>Estado</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>
</div>

<script>
let currentPage = 1;
let totalPages = 1;
const PAGE_SIZE = 200;

function toggleMenu() {
  const menu = document.getElementById("menu");
  menu.style.display = menu.style.display === "flex" ? "none" : "flex";
}

function toggleTheme() {
  const html = document.documentElement;
  html.dataset.theme = html.dataset.theme === "light" ? "dark" : "light";
}

let currentSimulationId = null;

async function startSimulation(e) {
  e.preventDefault();

  const scenario = document.getElementById("scenario").value;
  const btn = document.getElementById("btn-simular");
  const loader = document.getElementById("sim-loader");
  const stopBtn = document.getElementById("btn-stop");

  // UI: bloquear botón + mostrar loader + mostrar botón de parar
  btn.disabled = true;
  btn.innerText = "Simulando...";
  loader.style.display = "inline-block";
  stopBtn.style.display = "inline-block";

  document.getElementById("sim-result").innerHTML =
    `<div style="background:#fff7cc; padding:10px; border-radius:6px; color:#856404;">
       ⏳ Ejecutando simulación...
     </div>`;

  const res = await fetch("{{ backend }}/api/simulations", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ scenario })
  });

  const data = await res.json();

  // Si ya hay una simulación en curso
  if (res.status === 409) {
    document.getElementById("sim-result").innerHTML =
      `<div style="background:#f8d4d4; padding:10px; border-radius:6px; color:#721c24;">
         ❌ Ya hay una simulación en ejecución. Espera a que termine.
       </div>`;
    resetSimulationUI();
    return;
  }

  // Guardamos ID de la simulación para poder cancelarla
  currentSimulationId = data.simulation?.id || null;

  // IMPORTANTE: NO mostrar mensaje de éxito aquí
  // IMPORTANTE: NO llamar a resetSimulationUI()
  // IMPORTANTE: NO actualizar historial aquí

  // Esperar a que el backend termine k6
  waitForSimulationToFinish(currentSimulationId);
}

function resetSimulationUI() {
  const btn = document.getElementById("btn-simular");
  const loader = document.getElementById("sim-loader");
  const stopBtn = document.getElementById("btn-stop");

  btn.disabled = false;
  btn.innerText = "Iniciar simulación";
  loader.style.display = "none";
  stopBtn.style.display = "none";

  currentSimulationId = null;
}

async function stopSimulation() {
  if (!currentSimulationId) return;

  const res = await fetch(`{{ backend }}/api/simulations/${currentSimulationId}/cancel`, {
    method: "POST"
  });

  const data = await res.json();

  document.getElementById("sim-result").innerHTML =
    `<div style="background:#f8d4d4; padding:10px; border-radius:6px; color:#721c24;">
       ⛔ Simulación cancelada.
     </div>`;

  loadSimulations();
  resetSimulationUI();
}

async function loadSimulations() {
  const tbody = document.querySelector("#sim-table tbody");
  const container = document.getElementById("sim-history-container");

  tbody.innerHTML = "";

  try {
    const res = await fetch("{{ backend }}/api/simulations");
    const data = await res.json();

    if (!data || data.length === 0) {
      container.style.display = "none";
      return;
    }

    container.style.display = "block";

    data.forEach(sim => {
      const tr = document.createElement("tr");

      const color =
        sim.status === "completed" ? "#d4f8d4" :
        sim.status === "error" ? "#f8d4d4" :
        sim.status === "cancelled" ? "#ffe0b3" :
        "#fff7cc"; // running

      tr.style.background = color;

      tr.innerHTML = `
        <td>${sim.created_at}</td>
        <td>${sim.scenario}</td>
        <td>${sim.duration.toFixed(1)}</td>
        <td>${sim.avg_latency_ms.toFixed(1)}</td>
        <td>${sim.vus}</td>
        <td>${sim.throughput.toFixed(1)}</td>
        <td>${sim.status}</td>
      `;

      tbody.appendChild(tr);
    });

  } catch (e) {
    container.style.display = "none";
  }
}

function waitForSimulationToFinish(simId) {
  const interval = setInterval(async () => {
    const res = await fetch(`{{ backend }}/api/simulations/${simId}`);
    const sim = await res.json();

    if (sim.status !== "running") {
      clearInterval(interval);

      // Mostrar resultado final
      if (sim.status === "completed") {
        document.getElementById("sim-result").innerHTML =
          `<div style="background:#d4f8d4; padding:10px; border-radius:6px; color:#155724;">
             ✅ Simulación completada.
           </div>`;
      } else if (sim.status === "cancelled") {
        document.getElementById("sim-result").innerHTML =
          `<div style="background:#ffe0b3; padding:10px; border-radius:6px; color:#8a6d3b;">
             ⛔ Simulación cancelada.
           </div>`;
      } else {
        document.getElementById("sim-result").innerHTML =
          `<div style="background:#f8d4d4; padding:10px; border-radius:6px; color:#721c24;">
             ❌ Error en la simulación.
           </div>`;
      }

      // Ahora sí: actualizar historial y restaurar UI
      loadSimulations();
      resetSimulationUI();
      loadPatients();
    }
  }, 1000);
}

async function loadPatients() {
  try {
    const offset = (currentPage - 1) * PAGE_SIZE;

    const res = await fetch(`{{ backend }}/api/patients?limit=${PAGE_SIZE}&offset=${offset}`);
    const data = await res.json();

    const totalCountHeader = res.headers.get("X-Total-Count");
    const totalCount = totalCountHeader ? parseInt(totalCountHeader) : data.length;

    totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

    document.getElementById("page-number").innerText = currentPage;
    document.getElementById("total-pages").innerText = totalPages;

    const tbody = document.querySelector("#patients-table tbody");
    tbody.innerHTML = "";

    data.forEach(p => {
      const tr = document.createElement("tr");
      const triageClass = "triage-" + String(p.TriageAsignado || "").toLowerCase();

      tr.innerHTML = `
        <td>${p.id ?? ""}</td>
        <td>${p.device_id ?? ""}</td>
        <td>${p.device_victim_seq ?? ""}</td>
        <td>${p.Edad ?? ""}</td>
        <td>${p.Genero ?? ""}</td>
        <td>${p.LesionPrincipal ?? ""}</td>
        <td class="${triageClass}">${p.TriageAsignado ?? ""}</td>
        <td>${p.estado ?? ""}</td>
      `;
      tbody.appendChild(tr);
    });

  } catch (e) {
    console.error("Error cargando pacientes", e);
  }
}

function reloadPatients() {
  currentPage = 1;
  loadPatients();
}

function goFirst() {
  if (currentPage !== 1) {
    currentPage = 1;
    loadPatients();
  }
}

function goLast() {
  if (currentPage !== totalPages) {
    currentPage = totalPages;
    loadPatients();
  }
}

function goPrev() {
  if (currentPage > 1) {
    currentPage--;
    loadPatients();
  }
}

function goNext() {
  if (currentPage < totalPages) {
    currentPage++;
    loadPatients();
  }
}

function goToPage() {
  const input = document.getElementById("goto-page");
  const p = parseInt(input.value);
  if (!isNaN(p) && p >= 1 && p <= totalPages) {
    currentPage = p;
    loadPatients();
  }
}

loadPatients();
loadSimulations();
</script>

</body>
</html>
"""

# @app.get("/")
# def index():
#     return render_template_string(TEMPLATE, backend=BACKEND_URL)

@app.get("/")
def index():
    logo_url = url_for('static', filename='imgs/LogoSIMV.png')
    return render_template_string(TEMPLATE, backend=BACKEND_URL, logo_url=logo_url)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



