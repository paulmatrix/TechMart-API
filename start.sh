#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h db -p 5432 -U postgres; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is up - executing command"

# Make migrations
echo "Making migrations..."
python manage.py makemigrations --noinput

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
python manage.py shell -c "
try:
    from django.contrib.auth.models import User
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@techmart.com', 'admin1234')
        print('Superuser created: admin/admin1234')
    else:
        print('Superuser already exists')
except Exception as e:
    print(f'Error creating superuser: {e}')
    print('Continuing without superuser creation...')
"

# Start the server
echo "Starting server..."
exec "$@"
