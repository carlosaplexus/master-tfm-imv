# ================================
# CONFIGURACIÓN GENERAL
# ================================
REGISTRY=https://hub.docker.com/r/caedockerid
NAMESPACE=imv-simulacion
AWS_REGION=us-east-1
CLUSTER_NAME=eks-imv

BACKEND_IMAGE=$(REGISTRY)/backend:latest
FRONTEND_IMAGE=$(REGISTRY)/frontend:latest
GENERATOR_IMAGE=$(REGISTRY)/generador:latest

# ================================
# TESTS
# ================================

test-unit:
    @echo "▶ Ejecutando tests unitarios..."
    pytest backend/tests
    pytest generador/tests    

test-api:
    @echo "▶ Ejecutando tests de API..."
    python backend/tests_api/run_tests.py

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
    @echo "▶ Subiendo imágenes a GHCR..."
    echo $$GHCR_TOKEN | docker login ghcr.io -u TU_USUARIO --password-stdin
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

deploy:
    @echo "▶ Aplicando manifiestos Kubernetes..."
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/postgres/
    kubectl apply -f k8s/backend/
    kubectl apply -f k8s/frontend/

    @echo "▶ Esperando a que el LoadBalancer esté listo..."
    sleep 10
    kubectl get svc -n $(NAMESPACE)

url:
    @echo "▶ URL del frontend:"
    kubectl get svc frontend -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
    @echo ""


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
