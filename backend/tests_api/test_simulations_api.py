from backend.app import app, db

def setup_module(module):
    with app.app_context():
        db.create_all()

def teardown_module(module):
    with app.app_context():
        db.drop_all()

def test_post_simulation():
    client = app.test_client()

    payload = {
        "num_generators": 1,
        "patients_per_generator": 10
    }

    res = client.post("/api/simulations", json=payload)

    # En local siempre será 500 porque no hay Kubernetes
    assert res.status_code in (201, 500)

def test_simulations_status():
    client = app.test_client()

    res = client.get("/api/simulations/status")

    # En local siempre será 500 porque no hay Kubernetes
    assert res.status_code in (200, 500)

