import json
from backend.app import app, db

def setup_module(module):
    with app.app_context():
        db.create_all()

def teardown_module(module):
    with app.app_context():
        db.drop_all()

def test_post_patient():
    client = app.test_client()
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

def test_get_patients():
    client = app.test_client()
    res = client.get("/api/patients")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
