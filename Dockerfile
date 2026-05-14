FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gateways.py .
COPY common/ ./common/
RUN mkdir -p /app/usuarios /app/buisness /app/inventory /app/orders /app/rentas
COPY usuarios/ ./usuarios/
COPY buisness/ ./buisness/
COPY inventory/ ./inventory/
COPY orders/ ./orders/
COPY rentas/ ./rentas/

ENV PYTHONPATH=/app

CMD ["uvicorn", "gateways:app", "--host", "0.0.0.0", "--port", "8000"]