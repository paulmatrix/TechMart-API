#!/bin/bash

# TechMart API - Local CI Testing Script
# This script replicates the CI environment locally for testing

set -e  # Exit on any error

echo "🧪 TechMart API - Local CI Testing"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Set up environment variables (similar to CI)
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/test_techmart"
export DJANGO_SECRET_KEY="test-secret-key-for-local-ci-testing"
export DEBUG="True"
export ALLOWED_HOSTS="localhost,127.0.0.1"
export OIDC_RP_CLIENT_ID="test-client-id"
export OIDC_RP_CLIENT_SECRET="test-client-secret"
export OIDC_OP_AUTHORIZATION_ENDPOINT="https://test.auth0.com/authorize"
export OIDC_OP_TOKEN_ENDPOINT="https://test.auth0.com/oauth/token"
export OIDC_OP_USER_ENDPOINT="https://test.auth0.com/userinfo"
export OIDC_OP_JWKS_ENDPOINT="https://test.auth0.com/.well-known/jwks.json"
export OIDC_RP_REDIRECT_URI="http://localhost:8001/oidc/callback/"
export OIDC_RP_POST_LOGOUT_REDIRECT_URI="http://localhost:8001/oidc/logout/"
export OIDC_RP_SCOPES="openid email profile"
export AUTH0_DOMAIN="test.auth0.com"
export AUTH0_API_IDENTIFIER="https://techmart-api"
export AUTH0_ALGORITHMS="RS256"
export AFRICASTALKING_USERNAME="test-username"
export AFRICASTALKING_API_KEY="test-api-key"
export EMAIL_HOST_USER="test@example.com"
export EMAIL_HOST_PASSWORD="test-password"

print_status "Environment variables set"

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
    print_warning "PostgreSQL is not running. Please start PostgreSQL first:"
    echo "  - Docker: docker-compose up -d db"
    echo "  - Local: sudo service postgresql start"
    exit 1
fi

print_status "PostgreSQL is running"

# Create test database if it doesn't exist
psql -h localhost -U postgres -c "CREATE DATABASE test_techmart;" 2>/dev/null || true
print_status "Test database ready"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
print_status "Dependencies installed"

# Run migrations
echo "🗄️  Running migrations..."
python manage.py migrate --run-syncdb
print_status "Migrations completed"

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput > /dev/null 2>&1
print_status "Static files collected"

# Run tests
echo "🧪 Running tests..."
python manage.py test --verbosity=2
print_status "All tests passed"

# Run linting
echo "🔍 Running code linting..."
if command -v flake8 &> /dev/null; then
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    print_status "Linting completed"
else
    print_warning "flake8 not installed. Install with: pip install flake8"
fi

# Run security scan
echo "🔒 Running security scan..."
if command -v bandit &> /dev/null; then
    bandit -r . -f txt
    print_status "Security scan completed"
else
    print_warning "bandit not installed. Install with: pip install bandit"
fi

echo ""
echo "🎉 Local CI testing completed successfully!"
echo "Your code is ready for the CI/CD pipeline."
