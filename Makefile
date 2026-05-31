# ================================
# CONFIGURACIÓN GENERAL
# ================================
REGISTRY=caedockerid
NAMESPACE=imv-simulacion
AWS_REGION=us-east-1
CLUSTER_NAME=eks-imv
SCRIPT_CARGA_MANUAL=imv_escenario1.js

BACKEND_IMAGE=$(REGISTRY)/backend:latest
FRONTEND_IMAGE=$(REGISTRY)/frontend:latest
GENERATOR_IMAGE=$(REGISTRY)/generador:latest

# ================================
# TESTS
# ================================

# test-unit:
# 	@echo "▶ Ejecutando tests unitarios..."
# 	docker run --name unit-tests --env PYTHONPATH=/app -w /app backend/tests:latest sh -c "mkdir -p results/unit results/api results/coverage && pytest --cov --cov-report=xml:results/coverage.xml --cov-report=html:results/coverage --junit-xml=results/unit_result.xml --html=results/unit/index.html --self-contained-html -m unit || true"
# 	docker cp unit-tests:/app/results ./
# 	docker rm unit-tests || true


test-unit:
	mkdir -p results/unit results/api results/coverage
	pytest backend/tests \
		--cov \
		--cov-report=xml:results/coverage.xml \
		--cov-report=html:results/coverage \
		--junitxml=results/unit_result.xml \
		--html=results/unit/index.html --self-contained-html

test-api:
	mkdir -p results/unit results/api results/coverage
	pytest backend/tests_api \
		--junitxml=results/api_result.xml \
		--html=results/api/index.html --self-contained-html

test-generador:
	mkdir -p results/unit results/api results/coverage
	pytest generador/tests \
		--junitxml=results/generador_result.xml \
		--html=results/generador/index.html --self-contained-html

# test-api:
# 	docker stop apiserver || true
# 	docker rm --force apiserver || true
# 	docker stop api-tests || true
# 	docker rm --force api-tests || true
# 	docker network rm imv-test-api || true
# 	docker network create imv-test-api || true
# 	docker run -d --network imv-test-api --env PYTHONPATH=/app --name apiserver --env FLASK_APP=app/api.py -p 5001:5001 -w /app imv-app:latest flask run --host=0.0.0.0
# 	docker run --network imv-test-api --name api-tests --env PYTHONPATH=/app --env BASE_URL=http://apiserver:5001/ -w /pp imv-app:latest pytest --junit-xml=results/api_result.xml --html=results/api/index.html --self-contained-html -m api  || true
# 	docker cp api-tests:/app/results ./
# 	docker stop apiserver || true
# 	docker rm --force apiserver || true
# 	docker stop api-tests || true
# 	docker rm --force api-tests || true
# 	docker network rm imv-test-api || true
# test-api:
# 	@echo "▶ Ejecutando tests de API..."
# 	docker run --name api-tests --env PYTHONPATH=/app -w /app backend/tests_api:latest sh -c "mkdir -p results/unit results/api results/coverage && pytest backend/tests_api --junit-xml=results/api_result.xml --html=results/api/index.html --self-contained-html || true"
# 	docker cp api-tests:/app/results ./
# 	docker rm api-tests || true

test-e2e:
	@echo "▶ Ejecutando Cypress..."
	cd frontend && npx cypress run

tests: test-unit test-api test-e2e


# ================================
# DOCKER BUILD & PUSH
# ================================

build:
	@echo "▶ Construyendo imágenes Docker..."
	docker build -t $(BACKEND_IMAGE) backend/
	docker build -t $(FRONTEND_IMAGE) frontend/
	docker build -t $(GENERATOR_IMAGE) generador/

push:
	@echo "▶ Subiendo imágenes a DOCKERHUB..."
	echo $$DOCKERHUB_PSW | docker login -u $$DOCKERHUB_USR --password-stdin
	docker push $(BACKEND_IMAGE)
	docker push $(FRONTEND_IMAGE)
	docker push $(GENERATOR_IMAGE)


# ================================
# AWS ACADEMY LOGIN
# ================================

aws-login:
	@echo "▶ Autenticando en AWS Academy..."
	aws sts get-caller-identity
	aws eks update-kubeconfig --region $(AWS_REGION) --name $(CLUSTER_NAME)


# ================================
# DESPLIEGUE KUBERNETES
# ================================

# deploy:
# 	@echo "▶ Aplicando manifiestos Kubernetes..."
# 	kubectl apply -f k8s/namespace.yaml
# 	kubectl apply -f k8s/postgres/
# 	@echo "▶ Esperando a que el Postgres esté listo..."
# 	sleep 20
# 	kubectl apply -f k8s/backend/
# 	kubectl apply -f k8s/frontend/

deploy:
	@echo "▶ Aplicando manifiestos Kubernetes..."
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/postgres/

	@echo "▶ Esperando a que el Postgres esté listo..."
	sleep 20

	@echo "▶ Desplegando backend..."
	kubectl apply -f k8s/backend/

	@echo "▶ Desplegando frontend..."
	kubectl apply -f k8s/frontend/

	@echo "▶ Esperando a que el LoadBalancer frontend esté listo..."
	sleep 10

	@echo "▶ Servicios aplicacion desplegados..."
	kubectl get svc -n $(NAMESPACE)

	@echo "▶ Desplegando InfluxDB..."
	kubectl apply -f k8s/carga/influxdb/

	@echo "▶ Desplegando Grafana..."
	kubectl apply -f k8s/carga/grafana/

	@echo "▶ Esperando a que el LoadBalancer grafana esté listo..."
	sleep 10

	@echo "▶ Servicios con grafana desplegado..."	
	kubectl get svc -n $(NAMESPACE)

	@echo "▶ Generando ConfigMap automático con scripts K6..."
	kubectl create configmap k6-scripts --from-file=tests_carga/ -n imv-simulacion --dry-run=client -o yaml | kubectl apply -f -

#	@echo "▶ Ejecutando Job de K6 y realizando pruebas de carga..."
#	PIPELINE_ID=$(BUILD_NUMBER) envsubst < k8s/carga/k6/job-k6.yaml | kubectl apply -f -
#	PIPELINE_ID=$(BUILD_NUMBER) envsubst < k8s/carga/k6/job-k6.yaml | kubectl create -f -
#	JOB=$(PIPELINE_ID=$(BUILD_NUMBER) envsubst < k8s/carga/k6/job-k6.yaml | kubectl create -f - -o jsonpath='{.metadata.name}')
#	JOB_NAME=$$(PIPELINE_ID=$(BUILD_NUMBER) envsubst < k8s/carga/k6/job-k6.yaml | kubectl create -f - -o jsonpath='{.metadata.name}')

#	@echo "▶ Esperando a que el Job de K6 termine..."
#	JOB=$(kubectl get jobs -n imv-simulacion --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
#	kubectl wait --for=condition=complete job/$$JOB_NAME -n imv-simulacion --timeout=1h

	@echo "▶ Ejecutando Job de K6 y realizando pruebas de carga..."
	@JOB_NAME=$$(PIPELINE_ID=$(BUILD_NUMBER) envsubst < k8s/carga/k6/job-k6.yaml | kubectl create -f - -o jsonpath='{.metadata.name}'); \
	echo "Job creado: $$JOB_NAME"; \
	echo "▶ Esperando a que el Job termine..."; \
	kubectl wait --for=condition=complete job/$$JOB_NAME -n imv-simulacion --timeout=1h

	@echo "▶ Pruebas de carga completadas."	
	@echo "▶ Servicios desplegados y pruebas ejecutadas"
	kubectl get svc -n $(NAMESPACE)

urls:
	@echo "▶ URL del frontend:"
	kubectl get svc frontend -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
	@echo ""
	@echo "▶ URL de grafana:"
	kubectl get svc grafana -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
	@echo ""

deploy-job-pruebas1:
	kubectl apply -f k6-job-manual.yaml

deploy-job-pruebas2:
	kubectl create job k6-manual --image=grafana/k6 -- sh -c "k6 run /scripts/mi_script.js"

deploy-manual-independiente:
	kubectl run k6-manual -n imv-simulacion --image=grafana/k6:latest --restart=Never --command -- sh -c "k6 run /scripts/$(SCRIPT_CARGA_MANUAL)" --overrides='
	{
	"spec": {
		"volumes": [
		{
			"name": "k6-scripts",
			"configMap": { "name": "k6-scripts" }
		}
		],
		"containers": [
		{
			"name": "k6",
			"image": "grafana/k6:latest",
			"command": ["sh", "-c"],
			"args": ["k6 run /scripts/imv_escenarioX.js"],
			"volumeMounts": [
			{
				"name": "k6-scripts",
				"mountPath": "/scripts"
			}
			]
		}
		]
	}
	}'


# ================================
# LIMPIEZA
# ================================

clean:
	@echo "▶ Eliminando namespace completo..."
	kubectl delete namespace $(NAMESPACE) --ignore-not-found=true

# ================================
# FLUJO COMPLETO
# ================================

all: tests build push aws-login deploy url
	@echo "✔ Despliegue completo. Abre la URL anterior en tu navegador."
