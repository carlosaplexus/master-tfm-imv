from backend.app import generar_job_name

def test_generar_job_name():
    name = generar_job_name()
    assert name.startswith("sim-")
    assert len(name) > 4
