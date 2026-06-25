FROM python:3.11-slim

WORKDIR /app

COPY landlord/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/landlord /app/common
COPY landlord/ /app/landlord/
COPY common/ /app/common/

ENV PYTHONPATH=/app

CMD ["uvicorn", "landlord.main:app", "--host", "0.0.0.0", "--port", "8006"]