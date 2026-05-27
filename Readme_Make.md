🧠 Cómo usar este Makefile
1. Ejecutar todos los tests
make tests

2. Construir imágenes
make build

3. Subir imágenes a GHCR
make push

4. Autenticarse en AWS Academy
make aws-login

5. Desplegar todo en EKS
make deploy

6. Obtener la URL del frontend

make url
7. Ejecutarlo TODO de una vez
make all

🚀 Flujo completo recomendado
make tests
make build
make push
make aws-login
make deploy
make url
Abrir la URL y hacer un simulacro real

🧪 Cómo ejecutar los tests
🟦 Unitarios
make test-unit
🟧 API
make test-api
🟩 Cypress (E2E)
make test-e2e