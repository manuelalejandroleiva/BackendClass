FROM python:3.11-slim

WORKDIR /app

COPY usuarios/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/usuarios /app/common
COPY usuarios/ /app/usuarios/
COPY common/ /app/common/

ENV PYTHONPATH=/app

CMD ["uvicorn", "usuarios.main:app", "--host", "0.0.0.0", "--port", "8000"]