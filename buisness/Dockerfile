FROM python:3.11-slim

WORKDIR /app

COPY buisness/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/buisness /app/common
COPY buisness/ /app/buisness/
COPY common/ /app/common/

ENV PYTHONPATH=/app

CMD ["uvicorn", "buisness.main:app", "--host", "0.0.0.0", "--port", "8001"]