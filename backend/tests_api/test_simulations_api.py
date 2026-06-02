from backend.app import db

def test_list_patients_api(client):
    response = client.post("/api/patients", json={
        "device_id": "dev1",
        "device_victim_seq": 1,
        "Edad": 25,
        "Genero": "F",
        "LesionPrincipal": "Trauma",
        "TriageAsignado": "Verde",
        "FrecuenciaCardiaca": 90,
        "FrecuenciaRespiratoria": 18,
        "PresionSistolica": 110,
        "Glasgow": 15
    })

    assert response.status_code == 201

    response = client.get("/api/patients")
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 1
    assert data[0]["device_id"] == "dev1"

def test_run_simulation_invalid_scenario(client):
    res = client.post("/api/simulations", json={"scenario": "no_existe"})
    assert res.status_code == 400

def test_run_simulation_conflict(client):
    # Creamos una simulación en estado running
    with client.application.app_context():
        sim = client.application.Simulation(
            scenario="escenario_1",
            status="running"
        )
        db.session.add(sim)
        db.session.commit()

    res = client.post("/api/simulations", json={"scenario": "escenario_1"})
    assert res.status_code == 409

def test_run_simulation_success(client, monkeypatch):
    # Evitamos que se ejecute k6
    monkeypatch.setattr("subprocess.Popen", lambda *args, **kwargs: None)

    res = client.post("/api/simulations", json={"scenario": "escenario_1"})
    assert res.status_code == 201

    data = res.get_json()
    assert "simulation" in data
    assert data["simulation"]["status"] == "running"


