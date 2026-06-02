def test_post_patient(client):
    payload = {
        "device_id": "dev1",
        "device_victim_seq": 1,
        "Edad": 40,
        "Genero": "Mujer",
        "LesionPrincipal": "Fractura",
        "TriageAsignado": "Verde",
        "FrecuenciaCardiaca": 80,
        "FrecuenciaRespiratoria": 20,
        "PresionSistolica": 120,
        "Glasgow": 15
    }

    res = client.post("/api/patients", json=payload)
    assert res.status_code == 201

def test_get_patients(client):
    # Insertamos un paciente primero
    payload = {
        "device_id": "dev1",
        "device_victim_seq": 1,
        "Edad": 40,
        "Genero": "Mujer",
        "LesionPrincipal": "Fractura",
        "TriageAsignado": "Verde",
        "FrecuenciaCardiaca": 80,
        "FrecuenciaRespiratoria": 20,
        "PresionSistolica": 120,
        "Glasgow": 15
    }

    client.post("/api/patients", json=payload)

    # Ahora consultamos
    res = client.get("/api/patients")
    assert res.status_code == 200

    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["device_id"] == "dev1"

def test_post_patient_missing_fields(client):
    res = client.post("/api/patients", json={"device_id": "dev1"})
    assert res.status_code == 400

    data = res.get_json()
    assert "missing" in data
    assert "device_victim_seq" in data["missing"]

def test_post_patient_internal_error(client, monkeypatch):
    # Forzamos que db.session.add lance excepción
    def fake_add(obj):
        raise Exception("DB error")

    monkeypatch.setattr("backend.app.db.session.add", fake_add)

    payload = {
        "device_id": "dev1",
        "device_victim_seq": 1,
        "Edad": 40,
        "Genero": "M",
        "LesionPrincipal": "Trauma",
        "TriageAsignado": "Rojo",
        "FrecuenciaCardiaca": 80,
        "FrecuenciaRespiratoria": 20,
        "PresionSistolica": 120,
        "Glasgow": 15
    }

    res = client.post("/api/patients", json=payload)
    assert res.status_code == 500

def test_get_patients_pagination(client):
    # Insertamos 3 pacientes
    for i in range(3):
        client.post("/api/patients", json={
            "device_id": "dev1",
            "device_victim_seq": i + 1,
            "Edad": 30,
            "Genero": "M",
            "LesionPrincipal": "Trauma",
            "TriageAsignado": "Verde",
            "FrecuenciaCardiaca": 80,
            "FrecuenciaRespiratoria": 20,
            "PresionSistolica": 120,
            "Glasgow": 15
        })

    res = client.get("/api/patients?limit=1&offset=1")
    assert res.status_code == 200

    data = res.get_json()
    assert len(data) == 1

def test_get_max_seq(client):
    # Insertamos dos pacientes
    client.post("/api/patients", json={
        "device_id": "devX",
        "device_victim_seq": 5,
        "Edad": 20,
        "Genero": "F",
        "LesionPrincipal": "Trauma",
        "TriageAsignado": "Verde",
        "FrecuenciaCardiaca": 80,
        "FrecuenciaRespiratoria": 20,
        "PresionSistolica": 120,
        "Glasgow": 15
    })

    client.post("/api/patients", json={
        "device_id": "devX",
        "device_victim_seq": 7,
        "Edad": 22,
        "Genero": "F",
        "LesionPrincipal": "Trauma",
        "TriageAsignado": "Verde",
        "FrecuenciaCardiaca": 80,
        "FrecuenciaRespiratoria": 20,
        "PresionSistolica": 120,
        "Glasgow": 15
    })

    res = client.get("/api/patients/max-seq/devX")
    assert res.status_code == 200
    assert res.get_json()["max_seq"] == 7

