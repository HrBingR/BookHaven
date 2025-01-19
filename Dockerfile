FROM python:3.13

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r /app/backend/requirements.txt

RUN apt-get update && apt-get install -y tini && apt-get install openssl

COPY backend/ /app/backend
COPY frontend/dist/ /app/frontend/dist

RUN chmod +x /app/backend/entrypoint.sh

WORKDIR /app/backend

ENTRYPOINT ["/usr/bin/tini", "--", "/app/backend/entrypoint.sh"]