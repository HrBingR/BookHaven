#!/bin/bash

APP_PORT=${PORT:-5000}
NUM_WORKERS=${WORKERS:-1}

# Run migrations
echo "Checking and applying database migrations..."
python migrations.py

# Start the application
exec gunicorn -w $NUM_WORKERS -b 0.0.0.0:$APP_PORT main:app