from backend.app import db

def test_patient_model(client):
    app = client.application
    Patient = app.Patient

    with app.app_context():
        p = Patient(
            device_id="dev1",
            device_victim_seq=1,
            edad=30,
            genero="M",
            lesion_principal="Trauma",
            triage_asignado="Rojo",
            frecuencia_cardiaca=80,
            frecuencia_respiratoria=20,
            presion_sistolica=120,
            glasgow=15
        )

        db.session.add(p)
        db.session.commit()

        assert p.id is not None


def test_simulation_model(client):
    app = client.application
    Simulation = app.Simulation

    with app.app_context():
        s = Simulation(
            job_name="job-test-1",
            num_generators=2,
            patients_per_generator=100,
            status="created"
        )

        db.session.add(s)
        db.session.commit()

        assert s.id is not None



