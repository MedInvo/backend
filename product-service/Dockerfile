# This Dockerfile is used to build a Docker image for the order-service backend application.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

#test-one-09/11/26
