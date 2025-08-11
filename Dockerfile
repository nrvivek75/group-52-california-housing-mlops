# Multi-Service MLOps Docker Image
# This image contains: FastAPI API, MLflow, Prometheus, and Grafana
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    supervisor \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Prometheus
RUN wget https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.linux-amd64.tar.gz \
    && tar -xzf prometheus-2.47.0.linux-amd64.tar.gz \
    && mv prometheus-2.47.0.linux-amd64/prometheus /usr/local/bin/ \
    && rm -rf prometheus-2.47.0.linux-amd64*

# Download Grafana
RUN wget https://dl.grafana.com/oss/release/grafana-10.0.3.linux-amd64.tar.gz \
    && tar -xzf grafana-10.0.3.linux-amd64.tar.gz \
    && mv grafana-10.0.3 /usr/local/grafana \
    && rm grafana-10.0.3.linux-amd64.tar.gz

# Create necessary directories first
RUN mkdir -p logs grafana/provisioning/dashboards grafana/provisioning/datasources

# Copy application code and data
COPY src/ ./src/
COPY models/ ./models/
COPY mlruns/ ./mlruns/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY configs/ ./configs/

# Copy configuration files
COPY prometheus.yml ./prometheus.yml
COPY grafana/provisioning/dashboards/ ./grafana/provisioning/dashboards/
COPY grafana/provisioning/datasources/ ./grafana/provisioning/datasources/

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Make scripts executable
RUN chmod +x scripts/*.sh scripts/*.py

# Expose ports
EXPOSE 8001 5002 9090 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 