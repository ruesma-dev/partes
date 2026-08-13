# manifests/sv3/Dockerfile — sv3-partes: worker de persistencia (PG+SharePoint+Sigrid).
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 TZ=Europe/Madrid
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main_worker.py"]
