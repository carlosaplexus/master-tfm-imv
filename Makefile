# ================================
# TESTS
# ================================

test-unit:
	@echo "Ejecutando tests unitarios..."


test-api:
	@echo "Ejecutando tests de API..."


test-e2e:
	@echo "Ejecutando Cypress..."


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
	@echo "▶ URL del frontend"

