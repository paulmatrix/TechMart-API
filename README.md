# TechMart API

A Django REST Framework backend service for an Electronics Store.

## Project Structure

```
techmart-api/
├── config/                 # Django project settings
│   ├── __init__.py
│   ├── settings.py        # Main settings file
│   ├── urls.py           # URL configuration
│   ├── wsgi.py           # WSGI configuration
│   └── asgi.py           # ASGI configuration
├── catalog/               # Main app for models and APIs
│   ├── __init__.py
│   ├── models.py         # Database models
│   ├── views.py          # API views
│   ├── admin.py          # Django admin configuration
│   ├── apps.py           # App configuration
│   └── tests.py          # Unit tests
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## Setup

### Option 1: Docker (Recommended)

1. **Build and run with Docker:**
   ```bash
   docker-compose build
   docker-compose up
   ```

2. **Run migrations:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Access the application:**
   - Django: http://localhost:8000
   - Admin: http://localhost:8000/admin

For detailed Docker setup instructions, see [DOCKER_SETUP.md](DOCKER_SETUP.md).

### Option 2: Local Development

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `.env` file and update with your settings
   - Update database credentials for PostgreSQL connection
   - Update `SECRET_KEY` for production

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server:**
   ```bash
   python manage.py runserver
   ```

## Dependencies

- **Django 5.2.6** - Web framework
- **Django REST Framework 3.15.2** - API framework
- **psycopg2-binary 2.9.7** - PostgreSQL adapter
- **python-decouple 3.8** - Environment variable management
- **dj-database-url 2.1.0** - Database URL parsing
- **gunicorn 22.0.0** - WSGI server
- **django-mptt 0.16.0** - Modified Preorder Tree Traversal
- **django-cors-headers 4.3.1** - CORS handling
- **celery 5.3.6** - Task queue
- **redis 5.0.1** - Cache and message broker
- **requests 2.31.0** - HTTP library
- **Pillow 10.4.0** - Image processing

## Features

- Customer management (extends Django User)
- Hierarchical category system
- Product catalog
- Order management
- RESTful API endpoints
- PostgreSQL database
- Docker support
- Unit testing
- CI/CD pipeline ready

## API Endpoints

*Coming soon - will be documented as endpoints are implemented*

## Development

The project is configured for development with:
- Debug mode enabled by default
- SQLite fallback for local development
- CORS headers for frontend integration
- Comprehensive logging

## Production

For production deployment:
- Set `DEBUG=False`
- Configure proper `SECRET_KEY`
- Use PostgreSQL database
- Set up proper `ALLOWED_HOSTS`
- Configure static file serving
- Set up SSL/HTTPS
