📘 Plataforma de Simulación Digital IMV (EKS)

Este proyecto despliega una plataforma completa para simular carga digital en incidentes con múltiples víctimas (IMV).

Incluye:
Frontend (Flask + HTML/JS)
Backend (Flask + SQLAlchemy + Kubernetes API)
Generador (Python concurrente que envía pacientes sintéticos)
PostgreSQL (almacenamiento persistente)
Kubernetes Jobs para simulaciones masivas

La arquitectura está diseñada para ejecutarse en AWS EKS (AWS Academy).

🏗️ Arquitectura

Internet
   ↓
AWS LoadBalancer (ELB)
   ↓
Service frontend (LoadBalancer)
   ↓
Pods frontend
   ↓
Service backend (ClusterIP)
   ↓
Pods backend
   ↓
PostgreSQL (ClusterIP + PVC)
   ↓
Jobs generador (creados por backend)
   ↓
Pods generador → envían pacientes al backend

📦 1. Construir y publicar imágenes en GHCR

Autenticarse:
echo $GHCR_TOKEN | docker login ghcr.io -u TU_USUARIO --password-stdin

Backend
docker build -t ghcr.io/TU_USUARIO/backend:latest backend/
docker push ghcr.io/TU_USUARIO/backend:latest

Frontend
docker build -t ghcr.io/TU_USUARIO/frontend:latest frontend/
docker push ghcr.io/TU_USUARIO/frontend:latest

Generador
docker build -t ghcr.io/TU_USUARIO/generador:latest generador/
docker push ghcr.io/TU_USUARIO/generador:latest

📁 2. Estructura de carpetas

k8s/
├─ namespace.yaml
├─ postgres/
│   ├─ secret.yaml
│   ├─ pvc.yaml
│   ├─ deployment.yaml
│   ├─ service.yaml
├─ backend/
│   ├─ rbac.yaml
│   ├─ configmap.yaml
│   ├─ deployment.yaml
│   ├─ service.yaml
├─ frontend/
│   ├─ configmap.yaml
│   ├─ deployment.yaml
│   ├─ service.yaml

🚀 3. Despliegue en EKS
Crear namespace
kubectl apply -f k8s/namespace.yaml

Desplegar PostgreSQL
kubectl apply -f k8s/postgres/

Verificar:
kubectl get pods -n imv-simulacion
kubectl get svc -n imv-simulacion

Desplegar backend
kubectl apply -f k8s/backend/

Verificar:
kubectl get pods -n imv-simulacion -l app=backend
kubectl logs -n imv-simulacion -l app=backend

Desplegar frontend
kubectl apply -f k8s/frontend/

Verificar LoadBalancer:
kubectl get svc -n imv-simulacion

Obtendrás una URL como:
http://a1b2c3d4e5f6.elb.amazonaws.com

🧪 4. Probar el sistema
Ver pacientes

curl http://backend:5001/api/patients
Ver simulaciones

curl http://backend:5001/api/simulations/status
Acceder al frontend
Abre en el navegador:
http://<LOADBALANCER_URL>

🔥 5. Lanzar simulaciones desde el frontend
En la sección Simulaciones:
Elige número de generadores
Elige pacientes por generador
Pulsa Iniciar simulación

El backend creará Jobs en Kubernetes:
kubectl get jobs -n imv-simulacion
kubectl get pods -n imv-simulacion -l app=generator
Ver logs:
kubectl logs -n imv-simulacion <pod-name>

🗄️ 6. Base de datos
El backend crea automáticamente las tablas:
patients
simulations

Para inspeccionar PostgreSQL:
kubectl exec -it -n imv-simulacion postgres-0 -- psql -U postgres imv

🛠️ 7. Actualizar imágenes
Backend:
docker build -t ghcr.io/TU_USUARIO/backend:latest backend/
docker push ghcr.io/TU_USUARIO/backend:latest
kubectl rollout restart deployment backend -n imv-simulacion

Frontend:
docker build -t ghcr.io/TU_USUARIO/frontend:latest frontend/
docker push ghcr.io/TU_USUARIO/frontend:latest
kubectl rollout restart deployment frontend -n imv-simulacion

Generador:
docker build -t ghcr.io/TU_USUARIO/generador:latest generador/
docker push ghcr.io/TU_USUARIO/generador:latest

🧹 8. Borrar todo

kubectl delete namespace imv-simulacion

🎯 9. Notas importantes
El backend crea Jobs usando la imagen del generador definida en el ConfigMap.
El generador lee BACKEND_URL del entorno, no usa localhost.
El frontend solo necesita BACKEND_URL.
El backend requiere permisos RBAC para crear Jobs y leer logs.
Sobre IDs de la tabla de pacientes:
   - ID → contador global, siempre consecutivo
   - Seq → contador local por dispositivo, no consecutivo, no ordenado
   - Los hilos del generador hacen que los Seq lleguen desordenados
   - El backend ordena por ID, no por Seq