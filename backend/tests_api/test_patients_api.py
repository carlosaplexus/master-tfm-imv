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

