from flask import Flask, render_template_string, url_for
import os

app = Flask(__name__)

# LOCAL
# BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5001")
# CON DOCKER COMPOSE
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:5001")

TEMPLATE = """
<!doctype html>
<html lang="es" data-theme="light">
<head>
  <meta charset="utf-8">
  <title>Simulación de carga digital en IMV</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

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
    <label>Generadores:</label>
    <input type="number" id="num_generators" value="3" min="1" max="50">
    <label>Pacientes por generador:</label>
    <input type="number" id="patients_per_generator" value="10000" min="1">
    <button type="submit">Iniciar simulación</button>
  </form>
  <p id="sim-result"></p>

  <h3>Estado de simulaciones</h3>
  <button onclick="loadSimulations()">Actualizar estado</button>
  <table id="sim-table">
    <thead>
      <tr>
        <th>Job</th>
        <th>Estado</th>
        <th>Creado</th>
        <th>Historial</th>
        <th>Pods / Logs</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>
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

async function startSimulation(e) {
  e.preventDefault();
  const num = document.getElementById("num_generators").value;
  const per = document.getElementById("patients_per_generator").value;

  const res = await fetch("{{ backend }}/api/simulations", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      num_generators: parseInt(num),
      patients_per_generator: parseInt(per)
    })
  });

  const data = await res.json();
  document.getElementById("sim-result").innerText =
    res.ok ? `Simulación lanzada: ${data.jobs.join(", ")}` : `Error: ${JSON.stringify(data)}`;
  loadSimulations();
}

async function loadSimulations() {
  const tbody = document.querySelector("#sim-table tbody");
  tbody.innerHTML = "";
  try {
    const res = await fetch("{{ backend }}/api/simulations/status");
    const data = await res.json();

    data.forEach(sim => {
      const tr = document.createElement("tr");
      const history = sim.history ? `
        ID: ${sim.history.id}<br>
        Generadores: ${sim.history.num_generators}<br>
        Pacientes/gen: ${sim.history.patients_per_generator}<br>
        Estado hist.: ${sim.history.status}
      ` : "—";

      const podsHtml = sim.pods.map(p => `
        <b>${p.pod_name}</b> (${p.phase})<br>
        <pre>${p.log || ""}</pre>
      `).join("<hr>");

      tr.innerHTML = `
        <td>${sim.job_name}</td>
        <td>${sim.status}</td>
        <td>${sim.created_at || "—"}</td>
        <td>${history}</td>
        <td>${podsHtml}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    tbody.innerHTML = "<tr><td colspan='5'>Error al cargar simulaciones</td></tr>";
  }
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



