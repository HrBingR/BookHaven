#!/bin/bash

APP_PORT=${PORT:-5000}
NUM_WORKERS=${WORKERS:-1}

# Run migrations
echo "Checking and applying database migrations..."
if ! python migrations.py; then
    echo "Database migrations failed, exiting."
    exit 1
fi

# Start Gunicorn, Celery worker, and Celery Beat simultaneously
echo "Starting Gunicorn (Flask app), Celery worker, and Celery Beat..."

# Start all services in the background
gunicorn -w "$NUM_WORKERS" --config gunicorn_logging.py -b 0.0.0.0:"$APP_PORT" main:create_app &
celery -A celery_app.celery worker --loglevel=info &
celery -A celery_app.celery beat --loglevel=info &

# Wait for all services to complete
wait