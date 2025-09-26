# TechMart API


A Django REST Framework backend service for an Electronics Store with comprehensive CI/CD pipeline and production-ready deployment.

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

### Fresh Database Setup

If you need to start with a completely clean database:

1. **Stop containers and remove volumes:**
   ```bash
   docker-compose down -v
   ```

2. **Remove any existing migration files:**
   ```bash
   find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
   find . -path "*/migrations/*.pyc" -delete
   ```

3. **Start fresh containers:**
   ```bash
   docker-compose up -d db redis
   ```

4. **Create and apply migrations:**
   ```bash
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate
   ```

5. **Create superuser with default credentials:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```
   Use these credentials when prompted:
   - Email: `paulmwangikimaru@gmail.com`
   - Password: `admin1234`

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
   
   **Default Admin Credentials (for development):**
   - Email: `paulmwangikimaru@gmail.com`
   - Password: `admin1234`

4. **Access the application:**
   - Django: http://localhost:8000
   - Admin: http://localhost:8000/admin (Enhanced with custom styling and formatting)

For detailed Docker setup instructions, see [DOCKER_SETUP.md](DOCKER_SETUP.md).

For deployment instructions, see [RENDER_DEPLOYMENT_CHECKLIST.md](RENDER_DEPLOYMENT_CHECKLIST.md).

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
   - Copy `.env.example` to `.env`: `cp .env.example .env`
   - Update database credentials for PostgreSQL connection
   - Update `SECRET_KEY` for production
   - Configure Auth0/OIDC settings if using authentication

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```
   
   **Default Admin Credentials (for development):**
   - Email: `paulmwangikimaru@gmail.com`
   - Password: `admin1234`

6. **Run development server:**
   ```bash
   python manage.py runserver
   ```

7. **Access the application:**
   - Django: http://localhost:8000
   - Admin: http://localhost:8000/admin (Enhanced with custom styling and formatting)

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

## Admin Interface

The Django admin interface has been enhanced with:

- **Custom Styling**: Modern gradient design with improved visual hierarchy
- **Color-coded Status Badges**: Easy identification of active/inactive items and order statuses
- **Interactive Links**: Clickable links between related models (customers, orders, products)
- **Stock Management**: Visual stock status indicators (In Stock, Low Stock, Out of Stock)
- **Price Formatting**: Currency formatting with color coding
- **Statistics Display**: Product counts, order counts, and average prices
- **Optimized Queries**: Efficient database queries with select_related and prefetch_related
- **Inline Editing**: Quick editing capabilities for related items
- **Advanced Filtering**: Multiple filter options and search functionality



## Development

The project is configured for development with:
- Debug mode enabled by default
- SQLite fallback for local development
- CORS headers for frontend integration
- Comprehensive logging

## CI/CD Pipeline

This project includes a comprehensive CI/CD pipeline using GitHub Actions and Render deployment.

### Pipeline Overview

The CI/CD pipeline (`.github/workflows/ci-cd.yml`) includes:

1. **Build & Test (CI)**:
   - Runs on every push to `main` and `develop` branches
   - Runs on pull requests to `main`
   - Sets up Python 3.11 environment
   - Installs dependencies from `requirements.txt`
   - Runs Django migrations against PostgreSQL 14 service
   - Executes comprehensive test suite
   - Runs code linting with flake8
   - Performs security scans with Bandit and Safety

2. **Deploy (CD)**:
   - Triggers automatically after successful tests on `main` branch
   - Uses Render deploy hook for zero-downtime deployments
   - Includes error handling and deployment status reporting

3. **Security Scanning**:
   - Runs on pull requests
   - Scans for security vulnerabilities
   - Generates security reports

### Setting Up CI/CD

#### 1. GitHub Actions Setup

The pipeline is automatically configured when you push to GitHub. No additional setup required.

#### 2. Render Deployment Setup

To enable automatic deployment to Render:

1. **Create a Render Service**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Create a new "Web Service"
   - Connect your GitHub repository
   - Configure build and start commands:
     ```
     Build Command: pip install -r requirements.txt && python manage.py collectstatic --noinput
     Start Command: gunicorn config.wsgi:application
     ```

2. **Get Deploy Hook URL**:
   - In your Render service dashboard
   - Go to "Settings" → "Deploy Hook"
   - Copy the deploy hook URL

3. **Add GitHub Secret**:
   - Go to your GitHub repository
   - Navigate to "Settings" → "Secrets and variables" → "Actions"
   - Click "New repository secret"
   - Name: `RENDER_DEPLOY_HOOK`
   - Value: Paste the deploy hook URL from step 2

#### 3. Environment Variables for Render

Configure these environment variables in your Render service:

**Required:**
```bash
DATABASE_URL=postgresql://username:password@host:port/database
DJANGO_SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-render-app-url.onrender.com
```

**OIDC/Auth0 Configuration:**
```bash
OIDC_RP_CLIENT_ID=your-auth0-client-id
OIDC_RP_CLIENT_SECRET=your-auth0-client-secret
OIDC_OP_AUTHORIZATION_ENDPOINT=https://your-domain.auth0.com/authorize
OIDC_OP_TOKEN_ENDPOINT=https://your-domain.auth0.com/oauth/token
OIDC_OP_USER_ENDPOINT=https://your-domain.auth0.com/userinfo
OIDC_OP_JWKS_ENDPOINT=https://your-domain.auth0.com/.well-known/jwks.json
OIDC_RP_REDIRECT_URI=https://your-render-app-url.onrender.com/oidc/callback/
OIDC_RP_POST_LOGOUT_REDIRECT_URI=https://your-render-app-url.onrender.com/oidc/logout/
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_API_IDENTIFIER=https://techmart-api
AUTH0_ALGORITHMS=RS256
```

**Optional (for notifications):**
```bash
AFRICASTALKING_USERNAME=your-africas-talking-username
AFRICASTALKING_API_KEY=your-africas-talking-api-key
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
```

### Pipeline Workflow

```mermaid
graph LR
    A[Push to main] --> B[GitHub Actions CI]
    B --> C{Tests Pass?}
    C -->|Yes| D[Deploy to Render]
    C -->|No| E[❌ Build Failed]
    D --> F[✅ Deployed Successfully]
    
    G[Pull Request] --> H[CI + Security Scan]
    H --> I{All Checks Pass?}
    I -->|Yes| J[✅ Ready to Merge]
    I -->|No| K[❌ Fix Issues]
```

### Monitoring Deployments

- **GitHub Actions**: Check the "Actions" tab in your repository
- **Render Dashboard**: Monitor deployment status and logs
- **Application Health**: Use the `/health/` endpoint to verify deployment

### Troubleshooting

**Common Issues:**

1. **Tests Failing in CI**:
   - Check test logs in GitHub Actions
   - Ensure all environment variables are set correctly
   - Verify database migrations are working

2. **Deployment Not Triggering**:
   - Verify `RENDER_DEPLOY_HOOK` secret is set correctly
   - Check that tests are passing
   - Ensure you're pushing to the `main` branch

3. **Render Deployment Failing**:
   - Check Render service logs
   - Verify all required environment variables are set
   - Ensure build and start commands are correct

## Production

For production deployment:
- Set `DEBUG=False`
- Configure proper `SECRET_KEY`
- Use PostgreSQL database
- Set up proper `ALLOWED_HOSTS`
- Configure static file serving
- Set up SSL/HTTPS
- Use the CI/CD pipeline for automated deployments
