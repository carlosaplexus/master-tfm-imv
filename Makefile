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
  

test-api:
    @echo "▶ Ejecutando tests de API..."


test-e2e:
    @echo "▶ Ejecutando Cypress..."


tests: test-unit test-api test-e2e


# ================================
# DOCKER BUILD & PUSH
# ================================

build:
    @echo "▶ Construyendo imágenes Docker..."


push:
    @echo "▶ Subiendo imágenes a GHCR..."



# ================================
# AWS ACADEMY LOGIN
# ================================

aws-login:
    @echo "▶ Autenticando en AWS Academy..."



# ================================
# DESPLIEGUE KUBERNETES
# ================================

deploy:
    @echo "▶ Aplicando manifiestos Kubernetes..."


    @echo "▶ Esperando a que el LoadBalancer esté listo..."

url:
    @echo "▶ URL del frontend:"



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
