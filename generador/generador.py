import numpy as np
import pandas as pd
import os
import sys
import requests
import socket
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Forzar UTF-8 para print ---
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# ===========================================================
# CONFIGURACIÓN
# ===========================================================
MAX_EN_MEMORIA = 100000
NOMBRE_ARCHIVO = "IMV_sintetico.csv"

#LOCAL
BACKEND_URL = "http://localhost:5001/api/patients"
#PRE
#BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:5001/api/patients")
MAX_WORKERS = 50

print(">>> GENERADOR usando BACKEND_URL =", BACKEND_URL)

# ===========================================================
# GENERACIÓN AUTOMÁTICA DE DEVICE_ID
# ===========================================================

def obtener_device_id():
    """
    Intenta obtener un identificador único para este generador.
    Prioridad:
    1. Variable de entorno DEVICE_ID
    2. Hostname del contenedor/pod
    3. UUID persistente en archivo local
    """
    # 1. Variable de entorno
    env_id = os.getenv("DEVICE_ID")
    if env_id:
        return env_id

    # 2. Hostname del sistema (ideal en Kubernetes)
    try:
        hostname = socket.gethostname()
        if hostname:
            return f"device-{hostname}"
    except:
        pass

    # 3. UUID persistente
    uuid_file = ".device_uuid"
    if os.path.exists(uuid_file):
        with open(uuid_file, "r") as f:
            return f.read().strip()

    new_uuid = f"device-{uuid.uuid4()}"
    with open(uuid_file, "w") as f:
        f.write(new_uuid)
    return new_uuid


DEVICE_ID = obtener_device_id()
print(f"➡️ DEVICE_ID detectado automáticamente: {DEVICE_ID}")


# ===========================================================
# FUNCIONES GENERALES (idénticas)
# ===========================================================

def generar_constantes(gravedad):
    if gravedad == "Rojo":
        hr = np.random.normal(130, 15)
        rr = np.random.normal(30, 6)
        pas = np.random.normal(80, 10)
        glasgow = np.random.randint(3, 9)
    elif gravedad == "Amarillo":
        hr = np.random.normal(110, 10)
        rr = np.random.normal(24, 4)
        pas = np.random.normal(95, 10)
        glasgow = np.random.randint(9, 14)
    else:
        hr = np.random.normal(85, 10)
        rr = np.random.normal(18, 3)
        pas = np.random.normal(120, 15)
        glasgow = np.random.randint(14, 15)

    return {
        "FrecuenciaCardiaca": max(30, int(hr)),
        "FrecuenciaRespiratoria": max(5, int(rr)),
        "PresionSistolica": max(40, int(pas)),
        "Glasgow": glasgow
    }


def generar_lesion():
    lesiones = [
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
    probs = [0.10,0.15,0.12,0.05,0.10,0.08,0.10,0.15,0.05,0.10]
    return np.random.choice(lesiones, p=probs)


def clasificar_triage(c):
    if c["Glasgow"] < 9 or c["PresionSistolica"] < 90 or c["FrecuenciaRespiratoria"] > 30:
        return "Rojo"
    if c["FrecuenciaRespiratoria"] > 22 or c["FrecuenciaCardiaca"] > 110:
        return "Amarillo"
    return "Verde"


def generar_paciente_local(id_local):
    edad = np.random.randint(1, 90)
    genero = np.random.choice(["Hombre", "Mujer"])
    lesion = generar_lesion()

    gravedad_base = {
        "Traumatismo craneoencefálico": "Rojo",
        "Hemorragia externa": "Rojo",
        "Fractura abierta": "Amarillo",
        "Quemadura grave": "Rojo",
        "Contusión torácica": "Amarillo",
        "Politrauma": "Rojo",
        "Herida penetrante": "Amarillo",
        "Fractura cerrada": "Verde",
        "Intoxicación por humo": "Rojo",
        "Laceraciones múltiples": "Verde"
    }

    gravedad = gravedad_base[lesion]
    constantes = generar_constantes(gravedad)
    triage_final = clasificar_triage(constantes)

    return {
        "device_id": DEVICE_ID,
        "device_victim_seq": id_local,
        "Edad": edad,
        "Genero": genero,
        "LesionPrincipal": lesion,
        "TriageAsignado": triage_final,
        **constantes
    }


# ===========================================================
# ENVÍO AL BACKEND
# ===========================================================

# def enviar_paciente_backend(paciente):
#     try:
#         r = requests.post(BACKEND_URL, json=paciente, timeout=5)
#         return r.status_code == 201, r.status_code, r.text
#     except Exception as e:
#         return False, None, str(e)

# def enviar_paciente_backend(paciente):
#     import requests

#     try:
#         response = requests.post(BACKEND_URL, json=paciente, timeout=3)

#         # Si el backend responde OK
#         if response.status_code == 201:
#             try:
#                 return True, 201, response.json()
#             except Exception:
#                 return True, 201, response.text

#         # Si responde error
#         try:
#             return False, response.status_code, response.json()
#         except Exception:
#             return False, response.status_code, response.text

#     except Exception as e:
#         return False, -1, f"Error enviando paciente: {str(e)}"

def enviar_paciente_backend(paciente):
    import requests

    try:
        response = requests.post(BACKEND_URL, json=paciente, timeout=3)

        if response.status_code == 201:
            return True, 201, response.json()

        print("❌ Error HTTP:", response.status_code, response.text)
        return False, response.status_code, response.text

    except Exception as e:
        print("❌ Error de conexión:", type(e).__name__, str(e))
        return False, -1, str(e)


# ===========================================================
# GENERACIÓN + ENVÍO CONCURRENTE
# ===========================================================

def generar_y_enviar_lote(inicio_seq, cantidad):
    pacientes = [generar_paciente_local(inicio_seq + i) for i in range(cantidad)]

    ok_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(enviar_paciente_backend, p): p for p in pacientes}
        for fut in as_completed(futures):
            ok, status, resp = fut.result()
            if ok:
                ok_count += 1
            else:
                fail_count += 1

    return ok_count, fail_count


def generar_dataset_simulado(total_pacientes):
    print(f"\n➡️ Generando y enviando {total_pacientes} pacientes desde {DEVICE_ID}...\n")

    # Obtener el último seq usado para este device_id
    try:
        r = requests.get(f"http://localhost:5001/api/patients/max-seq/{DEVICE_ID}", timeout=3)
        inicio_seq = r.json().get("max_seq", 0) + 1
        print(f"➡️ Último seq en backend: {inicio_seq - 1}, empezando en {inicio_seq}")
    except Exception as e:
        print("❌ No se pudo obtener max_seq del backend:", e)
        inicio_seq = 1

    pacientes_generados = 0
    seq_actual = inicio_seq

    total_ok = 0
    total_fail = 0

    while pacientes_generados < total_pacientes:
        restantes = total_pacientes - pacientes_generados
        lote = min(restantes, MAX_EN_MEMORIA)

        ok, fail = generar_y_enviar_lote(seq_actual, lote)

        pacientes_generados += lote
        seq_actual += lote
        total_ok += ok
        total_fail += fail

        print(f"Lote enviado: OK={ok}, Fallidos={fail}")

    print(f"\n✔️ Total enviados OK: {total_ok}")
    print(f"❌ Total fallidos: {total_fail}")


# ===========================================================
# EJECUCIÓN
# ===========================================================
if __name__ == "__main__":
    generar_dataset_simulado(250)
