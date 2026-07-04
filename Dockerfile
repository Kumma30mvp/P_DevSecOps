# Imagen base ligera y con versiones fijadas (reproducible para SCA/container scan)
FROM python:3.12-slim

# Buenas practicas de runtime de Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Actualiza los paquetes del SO base para reducir CVEs del sistema operativo
# detectados por Trivy image (mitigacion de container scanning).
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias primero (mejor uso de cache de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el codigo de la aplicacion
COPY app/ ./app/

# Crear y usar un usuario no-root (reduce hallazgos en container scanning)
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Healthcheck con Python puro (urllib) para no depender de curl,
# que python:3.12-slim no incluye por defecto.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else sys.exit(1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
