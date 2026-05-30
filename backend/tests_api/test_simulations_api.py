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



