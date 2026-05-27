import numpy as np
import pandas as pd
import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Forzar UTF-8 para print ---
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# ===========================================================
# CONFIGURACIÓN
# ===========================================================
MAX_EN_MEMORIA = 100000          # número máximo por lote
NOMBRE_ARCHIVO = "IMV_sintetico.csv"

BACKEND_URL = "http://localhost:5001/api/patients"  # URL del backend
DEVICE_ID = "simulator-pod-1"    # identifica este generador/dispositivo
MAX_WORKERS = 50                 # hilos concurrentes para enviar pacientes


# ===========================================================
# FUNCIONES GENERALES (idénticas + device info)
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
    """
    id_local: número incremental de víctima en ESTE dispositivo
    """
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

    # Estructura pensada para el backend
    paciente = {
        "device_id": DEVICE_ID,
        "device_victim_seq": id_local,
        "Edad": edad,
        "Genero": genero,
        "LesionPrincipal": lesion,
        "TriageAsignado": triage_final,
        **constantes
    }

    return paciente


# ===========================================================
# ENVÍO AL BACKEND
# ===========================================================

def enviar_paciente_backend(paciente):
    """
    Envía un paciente al backend.
    Devuelve (ok: bool, status_code, respuesta_texto)
    """
    try:
        r = requests.post(BACKEND_URL, json=paciente, timeout=5)
        if r.status_code == 201:
            return True, r.status_code, r.text
        else:
            return False, r.status_code, r.text
    except Exception as e:
        return False, None, str(e)


# ===========================================================
# GENERACIÓN + ENVÍO CONCURRENTE
# ===========================================================

def generar_y_enviar_lote(inicio_seq, cantidad, guardar_csv=False, es_primer_lote=False):
    """
    Genera 'cantidad' pacientes a partir de un contador local (inicio_seq)
    y los envía concurrentemente al backend.
    Opcionalmente, guarda también en CSV.
    """
    print(f"   → Generando lote desde seq={inicio_seq} cantidad={cantidad}...")

    pacientes = [generar_paciente_local(inicio_seq + i) for i in range(cantidad)]

    # Envío concurrente al backend
    print(f"   → Enviando lote al backend con {MAX_WORKERS} hilos...")
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

    print(f"      ✔️ Enviados OK: {ok_count} | ❌ Fallidos: {fail_count}")

    # Opcional: guardar también en CSV local
    if guardar_csv:
        df = pd.DataFrame(pacientes)
        df.to_csv(
            NOMBRE_ARCHIVO,
            index=False,
            mode='a',
            header=es_primer_lote,
            encoding="utf-8-sig"
        )
        print(f"      💾 Lote guardado en CSV ({NOMBRE_ARCHIVO})")

    return ok_count, fail_count


def generar_dataset_simulado(total_pacientes, guardar_csv=False):
    """
    Genera pacientes y los envía al backend en lotes,
    simulando un dispositivo (DEVICE_ID) con un contador local.
    """
    if guardar_csv and os.path.exists(NOMBRE_ARCHIVO):
        os.remove(NOMBRE_ARCHIVO)

    print(f"\n➡️ Generando y enviando {total_pacientes} pacientes desde {DEVICE_ID}...")
    print(f"➡️ Límite por lote: {MAX_EN_MEMORIA}")
    print(f"➡️ Envío concurrente con {MAX_WORKERS} hilos.\n")

    pacientes_generados = 0
    batch_id = 1
    seq_actual = 1  # contador local de víctima en este dispositivo

    total_ok = 0
    total_fail = 0

    while pacientes_generados < total_pacientes:
        restantes = total_pacientes - pacientes_generados
        lote = min(restantes, MAX_EN_MEMORIA)

        print(f"--- Lote {batch_id} ({lote} pacientes) ---")
        ok, fail = generar_y_enviar_lote(
            inicio_seq=seq_actual,
            cantidad=lote,
            guardar_csv=guardar_csv,
            es_primer_lote=(batch_id == 1)
        )

        pacientes_generados += lote
        seq_actual += lote
        batch_id += 1
        total_ok += ok
        total_fail += fail

    print(f"\n✔️ Total pacientes generados: {pacientes_generados}")
    print(f"✔️ Total enviados OK: {total_ok}")
    print(f"❌ Total fallidos: {total_fail}")


# ===========================================================
# EJEMPLO DE USO
# ===========================================================
if __name__ == "__main__":
    # Ejemplo: generar y enviar 10.000 pacientes desde este "dispositivo"
    generar_dataset_simulado(10_000, guardar_csv=False)
