#!/bin/bash

set -e

APP_PORT="${APP_PORT:-5000}"
ENABLE_HTTPS="${ENABLE_HTTPS:-false}"
SSL_CERT_FILE="/ssl/${SSL_CERT_FILE:-}"
SSL_KEY_FILE="/ssl/${SSL_KEY_FILE:-}"
CELERY_LOG_LEVEL="${CELERY_LOG_LEVEL:-info}"

source .venv/bin/activate

echo "Checking and applying database migrations..."
if ! python migrations.py; then
    echo "Database migrations failed, exiting."
    exit 1
fi

if [ "$ENABLE_HTTPS" = "true" ]; then
    if [ -f "$SSL_CERT_FILE" ] && [ -f "$SSL_KEY_FILE" ]; then
        echo "Starting uvicorn (single worker) with HTTPS..."
        uvicorn asgi:asgi_app \
            --host 0.0.0.0 \
            --port "$APP_PORT" \
            --workers 1 \
            --ssl-certfile "$SSL_CERT_FILE" \
            --ssl-keyfile "$SSL_KEY_FILE" &
    else
        echo "ERROR: HTTPS is enabled but the SSL_CERT_FILE or SSL_KEY_FILE is missing. Exiting..."
        exit 1
    fi
else
    echo "Starting uvicorn (single worker) without HTTPS..."
    uvicorn asgi:asgi_app --host 0.0.0.0 --port "$APP_PORT" --workers 1 &
fi

echo "Starting Celery and Celery Beat..."
celery -A celery_app.celery worker --loglevel="$CELERY_LOG_LEVEL" &
celery -A celery_app.celery beat --loglevel="$CELERY_LOG_LEVEL" &

wait