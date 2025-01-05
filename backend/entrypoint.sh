#!/bin/bash

APP_PORT=${PORT:-5000}

# Run migrations
echo "Checking and applying database migrations..."
python migrations.py

# Start the application
exec gunicorn -w 4 -b 0.0.0.0:$APP_PORT main:app