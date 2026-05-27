from flask import Flask, render_template_string

app = Flask(__name__)

BACKEND_URL = "http://localhost:5001"

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

    [data-theme="light"] {
      --bg: var(--bg-light);
      --text: var(--text-light);
      --card: var(--card-light);
    }

    [data-theme="dark"] {
      --bg: var(--bg-dark);
      --text: var(--text-dark);
      --card: var(--card-dark);
    }

    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 1rem;
      background: #b30000;
      color: white;
    }

    header img {
      height: 40px;
      margin-right: 10px;
    }

    .title {
      display: flex;
      align-items: center;
      font-size: 1.2rem;
      font-weight: bold;
    }

    nav {
      display: none;
      flex-direction: column;
      background: #8a0000;
      padding: 1rem;
    }

    nav a {
      color: white;
      text-decoration: none;
      margin: 0.5rem 0;
    }

    .hamburger {
      cursor: pointer;
      font-size: 1.5rem;
    }

    @media (min-width: 700px) {
      nav {
        display: flex !important;
        flex-direction: row;
        background: none;
      }
      nav a {
        margin: 0 1rem;
      }
      .hamburger {
        display: none;
      }
    }

    .container {
      padding: 1rem;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--card);
    }

    th, td {
      padding: 0.5rem;
      border: 1px solid #ccc;
    }

    th {
      background: #ddd;
    }

    .triage-rojo { color: red; font-weight: bold; }
    .triage-amarillo { color: #c7a600; font-weight: bold; }
    .triage-verde { color: green; font-weight: bold; }

    .toggle-theme {
      cursor: pointer;
      background: white;
      color: black;
      padding: 0.3rem 0.6rem;
      border-radius: 5px;
      font-size: 0.9rem;
    }
  </style>
</head>

<body>

<header>
  <div class="title">
    <img src="imgs/LogoSIMV.png">
    Simulación de carga digital en IMV
  </div>

  <div class="hamburger" onclick="toggleMenu()">☰</div>

  <nav id="menu">
    <a href="#" onclick="loadPatients()">Pacientes</a>
    <a href="#">Estadísticas</a>
    <a href="#">Configuración</a>
    <span class="toggle-theme" onclick="toggleTheme()">🌓</span>
  </nav>
</header>

<div class="container">
  <h2>Pacientes recibidos</h2>
  <button onclick="loadPatients()">Recargar</button>

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
function toggleMenu() {
  const menu = document.getElementById("menu");
  menu.style.display = menu.style.display === "flex" ? "none" : "flex";
}

function toggleTheme() {
  const html = document.documentElement;
  html.dataset.theme = html.dataset.theme === "light" ? "dark" : "light";
}

async function loadPatients() {
  let data = [];

  try {
    const res = await fetch("{{ backend }}/api/patients?limit=200");
    data = await res.json();
  } catch (e) {
    console.warn("Backend no disponible, usando datos de ejemplo");
    data = [
      {id: 1, device_id: "demo-1", device_victim_seq: 1, Edad: 30, Genero: "Hombre", LesionPrincipal: "Fractura", TriageAsignado: "Verde", estado: "registrado"},
      {id: 2, device_id: "demo-2", device_victim_seq: 5, Edad: 70, Genero: "Mujer", LesionPrincipal: "Politrauma", TriageAsignado: "Rojo", estado: "crítico"}
    ];
  }

  const tbody = document.querySelector("#patients-table tbody");
  tbody.innerHTML = "";

  data.forEach(p => {
    const tr = document.createElement("tr");
    const triageClass = "triage-" + p.TriageAsignado.toLowerCase();

    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${p.device_id}</td>
      <td>${p.device_victim_seq}</td>
      <td>${p.Edad}</td>
      <td>${p.Genero}</td>
      <td>${p.LesionPrincipal}</td>
      <td class="${triageClass}">${p.TriageAsignado}</td>
      <td>${p.estado}</td>
    `;
    tbody.appendChild(tr);
  });
}

loadPatients();
</script>

</body>
</html>
"""

@app.get("/")
def index():
    return render_template_string(TEMPLATE, backend=BACKEND_URL)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
