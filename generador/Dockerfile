FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY generador.py .

# Variables que Kubernetes puede sobrescribir
ENV TOTAL_PACIENTES=10000
ENV BACKEND_URL="http://backend:5001/api/patients"

CMD ["python", "generador.py"]

