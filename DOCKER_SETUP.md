# Docker Setup Guide for TechMart API

This guide provides step-by-step instructions for containerizing and running the TechMart API using Docker and docker-compose.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)

## Project Structure

```
techmart-api/
├── Dockerfile              # Docker image configuration
├── docker-compose.yml      # Multi-container setup
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── config/                 # Django project settings
├── catalog/               # Django app
└── manage.py              # Django management script
```

## Environment Configuration

The `.env` file contains the following variables:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration
DB_NAME=techmart
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

## Docker Services

### 1. Web Service (Django)
- **Base Image**: Python 3.11 slim
- **Port**: 8000
- **Command**: Gunicorn WSGI server
- **Dependencies**: PostgreSQL database

### 2. Database Service (PostgreSQL)
- **Image**: PostgreSQL 14
- **Port**: 5432
- **Database**: techmart
- **User**: postgres
- **Password**: postgres
- **Volume**: Persistent data storage

## Commands

### Build and Run

1. **Build the containers:**
   ```bash
   docker-compose build
   ```

2. **Run the project:**
   ```bash
   docker-compose up
   ```

3. **Run in detached mode (background):**
   ```bash
   docker-compose up -d
   ```

4. **View logs:**
   ```bash
   docker-compose logs -f
   ```

### Database Operations

1. **Run migrations:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

2. **Create superuser:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

3. **Access Django shell:**
   ```bash
   docker-compose exec web python manage.py shell
   ```

4. **Collect static files:**
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```

### Development Commands

1. **Run Django development server (instead of Gunicorn):**
   ```bash
   docker-compose exec web python manage.py runserver 0.0.0.0:8000
   ```

2. **Install new Python packages:**
   ```bash
   # Add to requirements.txt first, then:
   docker-compose build web
   docker-compose up -d
   ```

3. **Access PostgreSQL database directly:**
   ```bash
   docker-compose exec db psql -U postgres -d techmart
   ```

### Maintenance Commands

1. **Stop all services:**
   ```bash
   docker-compose down
   ```

2. **Stop and remove volumes (⚠️ This will delete all data):**
   ```bash
   docker-compose down -v
   ```

3. **Rebuild without cache:**
   ```bash
   docker-compose build --no-cache
   ```

4. **View running containers:**
   ```bash
   docker-compose ps
   ```

## Access Points

- **Django Application**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **PostgreSQL Database**: localhost:5432

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Check what's using the port
   lsof -i :8000
   lsof -i :5432
   
   # Stop conflicting services or change ports in docker-compose.yml
   ```

2. **Database connection issues:**
   ```bash
   # Check if database is ready
   docker-compose exec db pg_isready -U postgres
   
   # View database logs
   docker-compose logs db
   ```

3. **Permission issues:**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

4. **Container won't start:**
   ```bash
   # Check container logs
   docker-compose logs web
   docker-compose logs db
   
   # Rebuild containers
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

### Health Checks

The PostgreSQL service includes a health check that ensures the database is ready before the web service starts.

## Production Considerations

For production deployment:

1. **Update environment variables:**
   - Set `DEBUG=False`
   - Use a strong `SECRET_KEY`
   - Configure proper `ALLOWED_HOSTS`
   - Use secure database credentials

2. **Security:**
   - Use Docker secrets for sensitive data
   - Configure proper firewall rules
   - Use HTTPS with SSL certificates

3. **Performance:**
   - Use a reverse proxy (nginx)
   - Configure proper resource limits
   - Use production-ready database settings

4. **Monitoring:**
   - Set up logging aggregation
   - Monitor container health
   - Configure backup strategies

## Development Workflow

1. Make code changes
2. Test locally with `docker-compose up`
3. Run tests: `docker-compose exec web python manage.py test`
4. Commit changes
5. Deploy to staging/production

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment Guide](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
