import pytest
from backend.app import app, db, Patient, Simulation

# EN LOCAL
# @pytest.fixture
# def client():
#     with app.app_context():
#         db.create_all()
#         yield app.test_client()
#         db.session.commit()
#         db.session.remove()
#         db.drop_all()

@pytest.fixture
def client():
    # 1. Cambiar la URI ANTES de tocar la DB
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True

    # 2. Cerrar conexiones previas a PostgreSQL
    db.session.remove()
    db.engine.dispose()

    # 3. Re-crear las tablas en SQLite
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_patient_model(client):
    p = Patient(
        device_id="dev1",
        device_victim_seq=1,
        edad=30,
        genero="Hombre",
        lesion_principal="Fractura",
        triage_asignado="Verde",
        frecuencia_cardiaca=80,
        frecuencia_respiratoria=20,
        presion_sistolica=120,
        glasgow=15,
        estado="registrado"
    )
    db.session.add(p)
    db.session.commit()

    assert p.id is not None
    assert p.device_id == "dev1"


def test_simulation_model(client):
    s = Simulation(
        job_name="job-test",
        num_generators=3,
        patients_per_generator=100,
        status="Running"
    )
    db.session.add(s)
    db.session.commit()

    assert s.id is not None
    assert s.job_name == "job-test"
