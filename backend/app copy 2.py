import logging
import uuid
import os
from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from kubernetes import client, config
from flask_cors import CORS

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
    job_name = db.Column(db.String, nullable=False, unique=True)
    num_generators = db.Column(db.Integer, nullable=False)
    patients_per_generator = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    status = db.Column(db.String, nullable=False, default="created")

    def to_dict(self):
        return {
            "id": self.id,
            "job_name": self.job_name,
            "num_generators": self.num_generators,
            "patients_per_generator": self.patients_per_generator,
            "created_at": self.created_at.isoformat(),
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
    GENERATOR_IMAGE = os.getenv("GENERATOR_IMAGE", "tuimagen/generador:latest")
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

    # ==========================================================
    # ENDPOINTS SIMULACIONES (K8S)
    # ==========================================================
    @app.post("/api/simulations")
    def create_simulation():
        if not k8s_batch:
            return jsonify({"error": "Kubernetes no disponible"}), 500

        data = request.get_json(silent=True) or {}
        num_generators = int(data.get("num_generators", 1))
        patients_per_generator = int(data.get("patients_per_generator", 1000))

        jobs = []

        for i in range(num_generators):
            job_name = f"imv-generator-{int(datetime.utcnow().timestamp())}-{i}"

            job = client.V1Job(
                metadata=client.V1ObjectMeta(
                    name=job_name,
                    namespace=K8S_NAMESPACE,
                    labels={"app": "generator", "simulation": "imv"}
                ),
                spec=client.V1JobSpec(
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(labels={"app": "generator", "simulation": "imv"}),
                        spec=client.V1PodSpec(
                            restart_policy="Never",
                            containers=[
                                client.V1Container(
                                    name="generator",
                                    image=GENERATOR_IMAGE,
                                    env=[
                                        client.V1EnvVar(name="BACKEND_URL", value=BACKEND_URL_ENV),
                                        client.V1EnvVar(name="TOTAL_PACIENTES", value=str(patients_per_generator))
                                    ]
                                )
                            ]
                        )
                    ),
                    backoff_limit=0
                )
            )

            k8s_batch.create_namespaced_job(namespace=K8S_NAMESPACE, body=job)

            sim = Simulation(
                job_name=job_name,
                num_generators=1,
                patients_per_generator=patients_per_generator,
                status="created",
            )
            db.session.add(sim)
            jobs.append(job_name)

        db.session.commit()

        return jsonify({"message": "Simulación lanzada", "jobs": jobs}), 201

    @app.get("/api/simulations/status")
    def simulations_status():
        if not k8s_batch or not k8s_core:
            return jsonify({"error": "Kubernetes no disponible"}), 500

        jobs = k8s_batch.list_namespaced_job(namespace=K8S_NAMESPACE, label_selector="simulation=imv")
        result = []

        for job in jobs.items:
            job_name = job.metadata.name
            status = "unknown"
            if job.status.active:
                status = "running"
            if job.status.succeeded:
                status = "succeeded"
            if job.status.failed:
                status = "failed"

            sim = Simulation.query.filter_by(job_name=job_name).first()
            if sim:
                sim.status = status

            pods = k8s_core.list_namespaced_pod(
                namespace=K8S_NAMESPACE,
                label_selector=f"job-name={job_name}"
            )
            pod_logs = []
            for pod in pods.items:
                try:
                    log_text = k8s_core.read_namespaced_pod_log(
                        name=pod.metadata.name,
                        namespace=K8S_NAMESPACE,
                        tail_lines=20
                    )
                except Exception:
                    log_text = ""
                pod_logs.append({
                    "pod_name": pod.metadata.name,
                    "phase": pod.status.phase,
                    "log": log_text,
                })

            result.append({
                "job_name": job_name,
                "status": status,
                "created_at": job.metadata.creation_timestamp.isoformat() if job.metadata.creation_timestamp else None,
                "pods": pod_logs,
                "history": sim.to_dict() if sim else None,
            })

        db.session.commit()
        return jsonify(result)

    return app


# ==========================================================
# MAIN (solo producción)
# ==========================================================
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5001, debug=True)


