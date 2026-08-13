# manifests/sv2/Dockerfile — sv2-partes: worker de extraccion (Gemini primario).
# El Container App corre el worker (main_worker.py); el create lo fuerza con
# --command python --args main_worker.py. Mantiene main.py (HTTP) para test local.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 TZ=Europe/Madrid
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main_worker.py"]
