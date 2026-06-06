import logging
import threading
import uuid
import os
import json
import subprocess
import tempfile
import time

from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from kubernetes import client, config
from flask_cors import CORS
from flask_cors import cross_origin


# Diccionario global: simulation_id → subprocess.Popen
ACTIVE_SIMULATIONS = {}

# ==========================================================
# SQLAlchemy sin inicializar (para permitir app factory)
# ==========================================================
db = SQLAlchemy()


# ==========================================================
# MODELOS (fuera de create_app)
# ==========================================================
class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_id = db.Column(db.String, nullable=False)
    device_victim_seq = db.Column(db.Integer, nullable=False)

    edad = db.Column(db.Integer, nullable=False)
    genero = db.Column(db.String, nullable=False)
    lesion_principal = db.Column(db.String, nullable=False)
    triage_asignado = db.Column(db.String, nullable=False)

    frecuencia_cardiaca = db.Column(db.Integer, nullable=False)
    frecuencia_respiratoria = db.Column(db.Integer, nullable=False)
    presion_sistolica = db.Column(db.Integer, nullable=False)
    glasgow = db.Column(db.Integer, nullable=False)

    estado = db.Column(db.String, nullable=False, default="registrado")
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        db.UniqueConstraint("device_id", "device_victim_seq", name="ux_device_victim"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "device_victim_seq": self.device_victim_seq,
            "Edad": self.edad,
            "Genero": self.genero,
            "LesionPrincipal": self.lesion_principal,
            "TriageAsignado": self.triage_asignado,
            "FrecuenciaCardiaca": self.frecuencia_cardiaca,
            "FrecuenciaRespiratoria": self.frecuencia_respiratoria,
            "PresionSistolica": self.presion_sistolica,
            "Glasgow": self.glasgow,
            "estado": self.estado,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Simulation(db.Model):
    __tablename__ = "simulations"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    scenario = db.Column(db.String, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    avg_latency_ms = db.Column(db.Float, nullable=False)
    vus = db.Column(db.Integer, nullable=False)
    throughput = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, default="running")

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "scenario": self.scenario,
            "duration": self.duration,
            "avg_latency_ms": self.avg_latency_ms,
            "vus": self.vus,
            "throughput": self.throughput,
            "status": self.status,
        }


# ==========================================================
# APP FACTORY — SIN NADA QUE REQUIERA CONTEXTO
# ==========================================================
def create_app(test_config=None):
    app = Flask(__name__)

    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}}, expose_headers=["X-Total-Count"])

    # DB CONFIG
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/imv")
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    # Inicializar SQLAlchemy (sin crear tablas)
    db.init_app(app)

    # Exponer modelos para tests
    app.Patient = Patient
    app.Simulation = Simulation

    # Kubernetes config (solo carga objetos, no ejecuta nada)
    K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "imv-simulacion")
    BACKEND_URL_ENV = os.getenv("BACKEND_URL", "http://backend:5001/api/patients")

    try:
        config.load_incluster_config()
        k8s_batch = client.BatchV1Api()
        k8s_core = client.CoreV1Api()
    except Exception:
        k8s_batch = None
        k8s_core = None

    # Logging (no requiere contexto)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    class RequestIdFilter(logging.Filter):
        def filter(self, record):
            record.request_id = getattr(g, "request_id", "-")
            return True

    logger = logging.getLogger("backend")
    logger.addFilter(RequestIdFilter())

    @app.before_request
    def before_request():
        g.request_id = str(uuid.uuid4())
        logger.info("Nueva petición")

    @app.after_request
    def after_request(response):
        response.headers["X-Request-Id"] = g.request_id
        logger.info("Petición completada")
        return response

    # ==========================================================
    # ENDPOINTS PACIENTES
    # ========================================================== 
    @app.post("/api/patients")
    def register_patient():
        data = request.get_json(silent=True) or {}
        required = [
            "device_id", "device_victim_seq",
            "Edad", "Genero", "LesionPrincipal", "TriageAsignado",
            "FrecuenciaCardiaca", "FrecuenciaRespiratoria",
            "PresionSistolica", "Glasgow",
        ]
        missing = [k for k in required if k not in data]
        if missing:
            return jsonify({"error": "Campos requeridos faltantes", "missing": missing}), 400

        try:
            patient = Patient(
                device_id=data["device_id"],
                device_victim_seq=int(data["device_victim_seq"]),
                edad=int(data["Edad"]),
                genero=str(data["Genero"]),
                lesion_principal=str(data["LesionPrincipal"]),
                triage_asignado=str(data["TriageAsignado"]),
                frecuencia_cardiaca=int(data["FrecuenciaCardiaca"]),
                frecuencia_respiratoria=int(data["FrecuenciaRespiratoria"]),
                presion_sistolica=int(data["PresionSistolica"]),
                glasgow=int(data["Glasgow"]),
                estado="registrado",
            )
            db.session.add(patient)
            db.session.commit()
            return jsonify({"id": patient.id, "estado": patient.estado}), 201
        except Exception:
            db.session.rollback()
            return jsonify({"error": "Error interno"}), 500
  
    @app.get("/api/patients")
    def list_patients():
        limit = int(request.args.get("limit", 200))
        offset = int(request.args.get("offset", 0))

        total = db.session.query(func.count(Patient.id)).scalar()
        patients = Patient.query.order_by(Patient.id).limit(limit).offset(offset).all()

        response = jsonify([p.to_dict() for p in patients])
        response.headers["X-Total-Count"] = str(total)
        response.headers["Cache-Control"] = "no-store"
        return response
   
    @app.get("/api/patients/max-seq/<device_id>")
    def get_max_seq(device_id):
        max_seq = db.session.query(func.max(Patient.device_victim_seq)).filter_by(device_id=device_id).scalar()
        return jsonify({"max_seq": max_seq or 0})

    @app.get("/api/patients/<int:patient_id>")
    def get_patient(patient_id):
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": "Paciente no encontrado"}), 404
        return jsonify(patient.to_dict()), 200

    @app.put("/api/patients/<int:patient_id>")
    def update_patient(patient_id):
        data = request.get_json(silent=True) or {}

        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": "Paciente no encontrado"}), 404

        # Solo permitimos editar triage y estado
        if "triage" in data:
            patient.triage_asignado = data["triage"]

        if "estado" in data:
            patient.estado = data["estado"]

        db.session.commit()

        return jsonify(patient.to_dict()), 200


    # ==========================================================
    # ENDPOINTS SIMULACIONES CON K6 EN K8S
    # ==========================================================

    K6_SCRIPTS_DIR = os.getenv("K6_SCRIPTS_DIR", "./escenarios")

    SCENARIOS = {
        "escenario_1": "imv_escenario1.js",
        "escenario_2": "imv_escenario2.js",
        "escenario_3": "imv_escenario3.js",
        "escenario_4": "imv_escenario4.js",
    }

    @app.route("/api/simulations", methods=["POST"])
    @cross_origin()
    def run_simulation():
        data = request.get_json(silent=True) or {}
        scenario = data.get("scenario")

        if scenario not in SCENARIOS:
            return jsonify({"error": "Escenario no válido"}), 400

        # Bloqueo: solo una simulación a la vez
        running = Simulation.query.filter_by(status="running").first()
        if running:
            return jsonify({"error": "Ya hay una simulación en ejecución"}), 409

        script_path = os.path.join(K6_SCRIPTS_DIR, SCENARIOS[scenario])

        # Crear simulación en estado running
        sim = Simulation(
            scenario=scenario,
            duration=0,
            avg_latency_ms=0,
            vus=0,
            throughput=0,
            status="running"
        )
        db.session.add(sim)
        db.session.commit()

        # # Archivo temporal para summary
        # with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        #     summary_path = tmp.name

        RESULTS_DIR = "/tmp/k6-results"
        os.makedirs(RESULTS_DIR, exist_ok=True)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        summary_path = os.path.join(RESULTS_DIR, f"{scenario}-{timestamp}.json")

        print("K6 SUMMARY PATH:", summary_path)

        if app.config.get("TESTING"):
            # No lanzar k6 ni hilos en tests
            return jsonify({
                "message": "Simulación iniciada (modo test)",
                "simulation": sim.to_dict()
            }), 201

        cmd = [
            "k6", "run",
            "--summary-export", summary_path,
            script_path
        ]

        # Lanzar proceso k6 (NO bloqueante)
        # #process = subprocess.Popen(cmd)
        # process = subprocess.Popen(
        #     cmd,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        #     text=True
        # )

        # stdout, stderr = process.communicate()

        # print("K6 STDOUT:", stdout)
        # print("K6 STDERR:", stderr)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        def stream_logs(proc):
            for line in proc.stdout:
                print("K6:", line.strip())

        # Hilo para imprimir logs de k6 en tiempo real
        threading.Thread(target=stream_logs, args=(process,), daemon=True).start()

        ACTIVE_SIMULATIONS[sim.id] = process

        start_time = time.time()

        # Hilo para esperar a que termine k6 y procesar el summary sin bloqueo de flask
        threading.Thread(
            target=wait_and_finalize,
            args=(app, sim.id, summary_path, start_time),
            daemon=True
        ).start()

        return jsonify({"message": "Simulación iniciada", "simulation": sim.to_dict()}), 201

    
    @app.route("/api/simulations/<int:sim_id>/cancel", methods=["POST"])
    @cross_origin()
    def cancel_simulation(sim_id):
        sim = Simulation.query.get(sim_id)
        if not sim:
            return jsonify({"error": "Simulación no encontrada"}), 404

        if sim.status != "running":
            return jsonify({"error": "La simulación no está en ejecución"}), 400

        process = ACTIVE_SIMULATIONS.get(sim_id)
        if process:
            try:
                process.kill()
            except Exception as e:
                return jsonify({"error": f"No se pudo detener k6: {str(e)}"}), 500

            ACTIVE_SIMULATIONS.pop(sim_id, None)

        sim.status = "cancelled"
        db.session.commit()

        return jsonify({"message": "Simulación cancelada", "simulation": sim.to_dict()})
    
    @app.route("/api/simulations", methods=["GET"])
    @cross_origin()
    def list_simulations():
        sims = Simulation.query.order_by(Simulation.created_at.desc()).all()
        return jsonify([s.to_dict() for s in sims])
    
    @app.route("/api/simulations/<int:sim_id>", methods=["GET"])
    @cross_origin()
    def get_simulation(sim_id):
        sim = Simulation.query.get(sim_id)
        if not sim:
            return jsonify({"error": "Simulación no encontrada"}), 404
        return jsonify(sim.to_dict())

    @app.route("/api/simulations", methods=["OPTIONS"])
    def simulations_options():
        response = jsonify({})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response, 204

    return app
    
def wait_and_finalize(app, sim_id, summary_path, start_time):
    with app.app_context():
        process = ACTIVE_SIMULATIONS.get(sim_id)
        if not process:
            print("⚠️ No se encontró el proceso activo")
            return

        print(f"⏳ Esperando a que termine k6 (simulación {sim_id})...")
        process.wait()
        end_time = time.time()
        print(f"✔️ k6 ha terminado (simulación {sim_id})")

        sim = Simulation.query.get(sim_id)
        if not sim:
            print("❌ Simulación no encontrada en BD")
            return

        # Si fue cancelada, no procesamos summary
        if sim.status == "cancelled":
            print("⛔ Simulación cancelada, no se procesa summary")
            ACTIVE_SIMULATIONS.pop(sim_id, None)
            return

        # Leer summary
        try:
            with open(summary_path, "r") as f:
                summary = json.load(f)
        except Exception as e:
            print(f"❌ Error leyendo summary: {e}")
            sim.status = "error"
            db.session.commit()
            ACTIVE_SIMULATIONS.pop(sim_id, None)
            return

        metrics = summary.get("metrics", {})

        # Duración real (k6 no la exporta en tu caso)
        sim.duration = round(end_time - start_time, 2)

        # Latencia media
        sim.avg_latency_ms = metrics.get("http_req_duration", {}).get("avg", 0)

        # VUs máximos
        sim.vus = metrics.get("vus_max", {}).get("value", 0)

        # Throughput (req/s)
        sim.throughput = metrics.get("http_reqs", {}).get("rate", 0)

        sim.status = "completed"

        db.session.commit()
        ACTIVE_SIMULATIONS.pop(sim_id, None)

        print(f"🏁 Simulación {sim_id} finalizada y guardada en BD")


# ==========================================================
# MAIN 
# ==========================================================
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5001, debug=True)


