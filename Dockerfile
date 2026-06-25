FROM python:3.11-slim

# Evita que Python escriba archivos .pyc y fuerza que la salida de log sea directa
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Instalar dependencias usando la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto (No es necesario crear carpetas vacías antes de copiar)
COPY gateways.py .env ./
COPY common/ ./common/
COPY usuarios/ ./usuarios/
COPY buisness/ ./buisness/
COPY inventory/ ./inventory/
COPY orders/ ./orders/
COPY rentas/ ./rentas/
COPY landlord/ ./landlord/

# Exponer el puerto de la aplicación
EXPOSE 8000

# Comando de inicio limpio y sin texto extra
CMD ["uvicorn", "gateways:app", "--host", "0.0.0.0", "--port", "8000"]
