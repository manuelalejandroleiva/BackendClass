FROM python:3.11-slim

WORKDIR /app

COPY orders/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/orders /app/common
COPY orders/ /app/orders/
COPY common/ /app/common/

ENV PYTHONPATH=/app

CMD ["uvicorn", "orders.main:app", "--host", "0.0.0.0", "--port", "8003"]
