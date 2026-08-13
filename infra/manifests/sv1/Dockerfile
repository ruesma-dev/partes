# manifests/sv1/Dockerfile — sv1-partes: webhook (FastAPI) + Job de suscripcion.
# Imagen unica con dos entrypoints:
#   - Container App (webhook):  CMD por defecto -> main.py
#   - Container Apps Job (renovar suscripcion): override --command python --args main_subscribe.py
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 TZ=Europe/Madrid
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
