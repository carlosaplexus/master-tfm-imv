FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias necesarias para descargar y descomprimir k6
RUN apt-get update && apt-get install -y curl tar

# Instalar k6 versión 1.8.0
RUN curl -L https://github.com/grafana/k6/releases/download/v1.8.0/k6-v1.8.0-linux-amd64.tar.gz -o /tmp/k6.tar.gz \
    && tar -xzf /tmp/k6.tar.gz -C /tmp \
    && mv /tmp/k6-v1.8.0-linux-amd64/k6 /usr/bin/k6 \
    && chmod +x /usr/bin/k6 \
    && rm -rf /tmp/k6*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5001

CMD ["python", "app.py"]


