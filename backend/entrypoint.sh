#!/bin/bash

set -e

APP_PORT="${PORT:-5000}"
ENABLE_HTTPS="${ENABLE_HTTPS:-false}"
SSL_CERT_FILE="/ssl/${SSL_CERT_FILE:-}"
SSL_KEY_FILE="/ssl/${SSL_KEY_FILE:-}"
CELERY_LOG_LEVEL="${CELERY_LOG_LEVEL:-info}"

echo "Checking and applying database migrations..."
if ! python migrations.py; then
    echo "Database migrations failed, exiting."
    exit 1
fi

if [ "$ENABLE_HTTPS" = "true" ]; then
    if [ -f "$SSL_CERT_FILE" ] && [ -f "$SSL_KEY_FILE" ]; then
        echo "Starting $NUM_WORKERS gunicorn workers with HTTPS..."
        gunicorn -w 1 --worker-class gthread --certfile="$SSL_CERT_FILE" --keyfile="$SSL_KEY_FILE" --timeout 300 --config gunicorn_logging.py -b 0.0.0.0:"$APP_PORT" main:app &
    else
        echo "ERROR: HTTPS is enabled but the SSL_CERT_FILE or SSL_KEY_FILE is missing. Exiting..."
        exit 1
    fi
else
    echo "Starting $NUM_WORKERS gunicorn workers without HTTPS..."
    gunicorn -w 1 --timeout 300 --worker-class gthread --config gunicorn_logging.py -b 0.0.0.0:"$APP_PORT" main:app &
fi

echo "Starting Celery and Celery Beat..."
celery -A celery_app.celery worker --loglevel="$CELERY_LOG_LEVEL" &
celery -A celery_app.celery beat --loglevel="$CELERY_LOG_LEVEL" &

wait