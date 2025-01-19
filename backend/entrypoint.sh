#!/bin/bash

set -e

APP_PORT="${PORT:-5000}"
NUM_WORKERS="${WORKERS:-1}"
ENABLE_HTTPS="${ENABLE_HTTPS:-false}"
SSL_CERT_FILE="/ssl/${SSL_CERT_FILE:-}"
SSL_KEY_FILE="/ssl/${SSL_KEY_FILE:-}"

echo "Checking and applying database migrations..."
if ! python migrations.py; then
    echo "Database migrations failed, exiting."
    exit 1
fi

if [ "$ENABLE_HTTPS" = "true" ]; then
    if [ -f "$SSL_CERT_FILE" ] && [ -f "$SSL_KEY_FILE" ]; then
        echo "Starting $NUM_WORKERS gunicorn workers with HTTPS..."
        gunicorn -w "$NUM_WORKERS" --certfile="$SSL_CERT_FILE" --keyfile="$SSL_KEY_FILE" --config gunicorn_logging.py -b 0.0.0.0:"$APP_PORT" main:create_app &
    else
        echo "ERROR: HTTPS is enabled but the SSL_CERT_FILE or SSL_KEY_FILE is missing. Exiting..."
        exit 1
    fi
else
    echo "Starting $NUM_WORKERS gunicorn workers without HTTPS..."
    gunicorn -w "$NUM_WORKERS" --config gunicorn_logging.py -b 0.0.0.0:"$APP_PORT" main:create_app &
fi

echo "Starting Celery and Celery Beat..."
celery -A celery_app.celery worker --loglevel=info > /var/log/celery-worker.log 2>&1 &
celery -A celery_app.celery beat --loglevel=info > /var/log/celery-worker.log 2>&1 &

wait