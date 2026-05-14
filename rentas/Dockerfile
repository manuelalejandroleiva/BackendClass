FROM python:3.11-slim

WORKDIR /app

COPY rentas/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/rentas /app/common
COPY rentas/ /app/rentas/
COPY common/ /app/common/

ENV PYTHONPATH=/app

CMD ["uvicorn", "rentas.main:app", "--host", "0.0.0.0", "--port", "8004"]
