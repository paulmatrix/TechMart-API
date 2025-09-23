#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h db -p 5432 -U postgres; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is up - executing command"

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@techmart.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Start the server
echo "Starting server..."
exec "$@"
