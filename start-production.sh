#!/bin/bash

# Production startup script for Render deployment
# This script handles database migrations and static file collection
# without waiting for a specific database host

set -e  # Exit on any error

echo "Starting TechMart API production deployment..."

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the server
echo "Starting Gunicorn server..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
