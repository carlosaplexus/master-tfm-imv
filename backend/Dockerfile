FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl tar

RUN curl -fSL https://github.com/grafana/k6/releases/download/v0.52.0/k6-v0.52.0-linux-amd64.tar.gz -o /tmp/k6.tar.gz \
    && tar -xzf /tmp/k6.tar.gz -C /tmp \
    && mv /tmp/k6-v0.52.0-linux-amd64/k6 /usr/bin/k6 \
    && chmod +x /usr/bin/k6 \
    && rm -rf /tmp/k6*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["python", "app.py"]

