import pytest
from unittest.mock import patch
from generador.generador import (
    generar_constantes,
    generar_lesion,
    clasificar_triage,
    generar_paciente_local,
    enviar_paciente_backend,
    generar_y_enviar_lote,
    generar_dataset_simulado,
    obtener_device_id
)

# ============================================================
# 1. TESTS DE GENERACIÓN DE CONSTANTES
# ============================================================

def test_constantes_rojo():
    c = generar_constantes("Rojo")
    print(f"[INFO] Constantes ROJO generadas: {c}")
    assert 30 <= c["FrecuenciaCardiaca"] <= 200
    assert 5 <= c["FrecuenciaRespiratoria"] <= 60
    assert 40 <= c["PresionSistolica"] <= 200
    assert 3 <= c["Glasgow"] <= 8

def test_constantes_amarillo():
    c = generar_constantes("Amarillo")
    print(f"[INFO] Constantes AMARILLO generadas: {c}")
    assert 30 <= c["FrecuenciaCardiaca"]
    assert 5 <= c["FrecuenciaRespiratoria"]
    assert 40 <= c["PresionSistolica"]
    assert 9 <= c["Glasgow"] <= 13

def test_constantes_verde():
    c = generar_constantes("Verde")
    print(f"[INFO] Constantes VERDE generadas: {c}")
    assert 30 <= c["FrecuenciaCardiaca"]
    assert 5 <= c["FrecuenciaRespiratoria"]
    assert 40 <= c["PresionSistolica"]
    assert 14 <= c["Glasgow"] <= 15


# ============================================================
# 2. TESTS DE GENERACIÓN DE LESIONES
# ============================================================

def test_generar_lesion_valida():
    lesiones_validas = [
        "Traumatismo craneoencefálico",
        "Hemorragia externa",
        "Fractura abierta",
        "Quemadura grave",
        "Contusión torácica",
        "Politrauma",
        "Herida penetrante",
        "Fractura cerrada",
        "Intoxicación por humo",
        "Laceraciones múltiples"
    ]
    lesion = generar_lesion()
    print(f"[INFO] Lesión generada: {lesion}")
    assert lesion in lesiones_validas


# ============================================================
# 3. TESTS DE CLASIFICACIÓN DE TRIAGE
# ============================================================

def test_triage_rojo():
    c = {"Glasgow": 7, "PresionSistolica": 80, "FrecuenciaRespiratoria": 35}
    triage = clasificar_triage(c)
    print(f"[INFO] Triage calculado (ROJO): {triage}")
    assert triage == "Rojo"

def test_triage_amarillo():
    c = {
        "Glasgow": 12,
        "PresionSistolica": 110,
        "FrecuenciaRespiratoria": 24,
        "FrecuenciaCardiaca": 120
    }
    triage = clasificar_triage(c)
    print(f"[INFO] Triage calculado (AMARILLO): {triage}")
    assert triage == "Amarillo"

def test_triage_verde():
    c = {
        "Glasgow": 15,
        "PresionSistolica": 120,
        "FrecuenciaRespiratoria": 18,
        "FrecuenciaCardiaca": 80
    }
    triage = clasificar_triage(c)
    print(f"[INFO] Triage calculado (VERDE): {triage}")
    assert triage == "Verde"


# ============================================================
# 4. TESTS DE GENERACIÓN DE PACIENTES
# ============================================================

def test_generar_paciente():
    p = generar_paciente_local(10)
    print(f"[INFO] Paciente generado: {p}")
    assert p["device_victim_seq"] == 10
    assert 1 <= p["Edad"] <= 90
    assert p["Genero"] in ["Hombre", "Mujer"]
    assert "LesionPrincipal" in p
    assert p["TriageAsignado"] in ["Rojo", "Amarillo", "Verde"]


# ============================================================
# 5. TESTS DE ENVÍO AL BACKEND (MOCK)
# ============================================================

@patch("generador.generador.requests.post")
def test_envio_backend_ok(mock_post):
    mock_post.return_value.status_code = 201
    ok, status, resp = enviar_paciente_backend({"test": 1})
    print(f"[INFO] Backend fake OK → ok={ok}, status={status}, resp={resp}")
    assert ok is True
    assert status == 201

@patch("generador.generador.requests.post")
def test_envio_backend_fail(mock_post):
    mock_post.return_value.status_code = 500
    ok, status, resp = enviar_paciente_backend({"test": 1})
    print(f"[INFO] Backend fake FAIL → ok={ok}, status={status}, resp={resp}")
    assert ok is False
    assert status == 500


# ============================================================
# 6. TESTS DE GENERACIÓN DE LOTES
# ============================================================

@patch("generador.generador.enviar_paciente_backend")
def test_generar_y_enviar_lote(mock_envio):
    mock_envio.return_value = (True, 201, "OK")
    ok, fail = generar_y_enviar_lote(1, 20)
    print(f"[INFO] Lote generado: OK={ok}, FAIL={fail}")
    assert ok == 20
    assert fail == 0


# ============================================================
# 7. TESTS DE GENERACIÓN DE DATASET COMPLETO
# ============================================================

@patch("generador.generador.generar_y_enviar_lote")
def test_generar_dataset(mock_lote):
    mock_lote.return_value = (100, 0)
    generar_dataset_simulado(100)
    print("[INFO] Dataset simulado generado correctamente")
    mock_lote.assert_called()


# ============================================================
# 8. TESTS DE DEVICE ID
# ============================================================

def test_device_id():
    d = obtener_device_id()
    print(f"[INFO] Device ID generado: {d}")
    assert isinstance(d, str)
    assert len(d) > 5


# ============================================================
# 9. TESTS DE RENDIMIENTO
# ============================================================

import time

def test_rendimiento_generacion_1000_pacientes():
    inicio = time.time()
    for i in range(1000):
        generar_paciente_local(i)
    fin = time.time()
    duracion = fin - inicio
    print(f"\n[PERF] Tiempo para generar 1000 pacientes: {duracion:.4f} s")
    assert duracion < 1.5  # Ajusta según tu máquina

# ============================================================
# 10. TEST DE ESTRÉS
# ============================================================

def test_estres_10000_generaciones():
    inicio = time.time()
    for i in range(10000):
        generar_paciente_local(i)
    fin = time.time()
    duracion = fin - inicio
    print(f"\n[STRESS] Tiempo para generar 10.000 pacientes: {duracion:.4f} s")
    assert duracion < 15  # Ajusta según tu hardware

# ============================================================
# 11. TESTS DE CONCURRENCIA
# ============================================================

import concurrent.futures

def test_concurrencia_generacion():
    def worker(i):
        return generar_paciente_local(i)

    inicio = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(worker, range(500)))
    fin = time.time()

    print(f"\n[CONCURRENCY] 500 pacientes con 10 hilos: {fin - inicio:.4f} s")

    assert len(results) == 500
    assert all("Edad" in p for p in results)

# ============================================================
# 12. VALIDACIÓN DE DATOS
# ============================================================

def test_validacion_datos_generados():
    p = generar_paciente_local(1)

    assert isinstance(p["Edad"], int)
    assert 0 < p["Edad"] < 120

    assert p["Genero"] in ["Hombre", "Mujer"]

    assert isinstance(p["LesionPrincipal"], str)
    assert len(p["LesionPrincipal"]) > 0

    assert p["TriageAsignado"] in ["Rojo", "Amarillo", "Verde"]

# ============================================================
# 13. TESTS DE REGRESIÓN
# ============================================================

def test_regresion_campos_obligatorios():
    p = generar_paciente_local(5)
    campos = [
        "device_id",
        "device_victim_seq",
        "Edad",
        "Genero",
        "LesionPrincipal",
        "TriageAsignado"
    ]
    for campo in campos:
        assert campo in p

# ============================================================
# 14. TESTS DE BACKEND FAKE
# ============================================================

@patch("generador.generador.requests.post")
def test_backend_fake_respuesta_json(mock_post):
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"status": "ok", "id": 123}

    ok, status, resp = enviar_paciente_backend({"test": 1})

    assert ok is True
    assert status == 201
    assert resp == {"status": "ok", "id": 123}

# ============================================================
# 15. TESTS DE ERRORES CONTROLADOS
# ============================================================

@patch("generador.generador.requests.post")
def test_envio_backend_exception(mock_post):
    mock_post.side_effect = Exception("Error de red")

    ok, status, resp = enviar_paciente_backend({"test": 1})

    assert ok is False
    assert status == -1
    assert "Error" in resp
