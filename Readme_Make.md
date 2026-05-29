+ Preparacion del entorno
-----------------------------------------
1. Logarse en Github
2. Logarse en Dockerhub
3. Logarse en AWS Academy


+ Ejecutores
-----------------------------------------
1. Ejecutar todos los tests
        make tests

2. Construir imágenes
        make build

3. Subir imágenes a Github
        make push

4. Autenticarse en AWS Academy
        make aws-login

5. Desplegar todo en EKS
        make deploy

6. Obtener la URL del frontend
        make url

7. Ejecutarlo TODO de una vez
        make all

+ Flujo completo
-----------------------------------------
        make tests
        make build
        make push
        make aws-login
        make deploy
        make url

+ Test específicos
------------------------------------------
- Unitarios
    make test-unit
- API
    make test-api
- Cypress (E2E)
    make test-e2e