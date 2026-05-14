FROM python:3.11-slim

WORKDIR /app

COPY inventory/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/inventory /app/common
COPY inventory/ /app/inventory/
COPY common/ /app/common/

ENV PYTHONPATH=/app

CMD ["uvicorn", "inventory.main:app", "--host", "0.0.0.0", "--port", "8002"]
