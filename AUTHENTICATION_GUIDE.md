# TechMart API Authentication Guide

## Overview

The TechMart API implements a hybrid authentication system using **OpenID Connect (OIDC)** for user authentication and **JWT tokens** for API access. This provides secure, standards-based authentication while maintaining flexibility for different client types.

## Authentication Methods

### 1. OpenID Connect (OIDC)

**Primary authentication method** for web applications and user-facing clients.

#### OIDC Flow:
1. **Authorization Request**: Client redirects user to OIDC provider
2. **User Authentication**: User authenticates with OIDC provider
3. **Authorization Code**: Provider returns authorization code
4. **Token Exchange**: Client exchanges code for access/ID tokens
5. **User Info**: Client fetches user information
6. **API Access**: Client uses tokens to access API

#### OIDC Endpoints:
- **Authorization**: `GET /oidc/authenticate/`
- **Callback**: `POST /oidc/callback/`

### 2. JWT Tokens

**API access method** for programmatic clients and authenticated users.

#### JWT Endpoints:
- **Token Obtain**: `POST /api/token/`
- **Token Refresh**: `POST /api/token/refresh/`

## Authentication Levels

### Public Access (No Authentication Required)
- **Categories**: Read-only access to browse categories
- **Products**: Read-only access to browse products
- **API Documentation**: Swagger UI and ReDoc

### Authenticated Access (JWT Required)
- **Categories**: Create, update, delete categories
- **Products**: Create, update, delete products, manage stock

### OIDC Required Access (OIDC Authentication Required)
- **Orders**: Full CRUD operations
- **Customer Profiles**: Full CRUD operations

## Configuration

### Environment Variables

```env
# OIDC Provider Configuration
OIDC_RP_CLIENT_ID=techmart-api
OIDC_RP_CLIENT_SECRET=your-client-secret
OIDC_OP_AUTHORIZATION_ENDPOINT=https://your-oidc-provider.com/auth
OIDC_OP_TOKEN_ENDPOINT=https://your-oidc-provider.com/token
OIDC_OP_USER_ENDPOINT=https://your-oidc-provider.com/userinfo
OIDC_OP_JWKS_ENDPOINT=https://your-oidc-provider.com/.well-known/jwks.json
OIDC_RP_SIGN_ALGO=RS256
OIDC_RP_SCOPES=openid email profile
```

### Django Settings

```python
# Authentication backends
AUTHENTICATION_BACKENDS = [
    'catalog.auth_backends.TechMartOIDCAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# DRF Authentication
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

## Usage Examples

### 1. OIDC Authentication (Web Application)

```javascript
// Redirect to OIDC provider
window.location.href = '/oidc/authenticate/';

// Handle callback (automatic)
// User will be redirected back with authentication
```

### 2. JWT Token Authentication (API Client)

```bash
# Obtain JWT tokens
curl -X POST http://localhost:8001/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

# Use access token for API requests
curl -X GET http://localhost:8001/api/v1/products/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Refresh token when expired
curl -X POST http://localhost:8001/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}'
```

### 3. Python Client Example

```python
import requests

# Authenticate and get tokens
auth_response = requests.post('http://localhost:8001/api/token/', json={
    'username': 'your-username',
    'password': 'your-password'
})
tokens = auth_response.json()
access_token = tokens['access']

# Make authenticated API requests
headers = {'Authorization': f'Bearer {access_token}'}

# Create a product (requires authentication)
product_data = {
    'name': 'New Product',
    'sku': 'NEW-001',
    'description': 'A new product',
    'category': 1,
    'price': '99.99',
    'stock_quantity': 10
}
response = requests.post(
    'http://localhost:8001/api/v1/products/',
    json=product_data,
    headers=headers
)

# Browse products (public access)
response = requests.get('http://localhost:8001/api/v1/products/')
```

## User Management

### Automatic User Creation

When a user authenticates via OIDC for the first time:

1. **User Account**: Created automatically with OIDC claims
2. **Customer Profile**: Created with phone and address from OIDC claims
3. **Permissions**: Standard user permissions assigned

### User Profile Updates

On subsequent OIDC logins:

1. **User Information**: Updated with latest OIDC claims
2. **Profile Information**: Updated with latest phone/address
3. **Session**: Refreshed automatically

### OIDC Claims Mapping

```python
# OIDC Claims → Django User Fields
{
    'sub': 'unique-user-id',           # Used for user identification
    'email': 'user@example.com',       # → user.email
    'given_name': 'John',              # → user.first_name
    'family_name': 'Doe',              # → user.last_name
    'phone_number': '+1234567890',     # → profile.phone
    'address': '123 Main St'           # → profile.address
}
```

## Security Features

### 1. Token Security
- **JWT Access Tokens**: Short-lived (60 minutes)
- **JWT Refresh Tokens**: Longer-lived (7 days)
- **Token Rotation**: Refresh tokens are rotated on use
- **Blacklisting**: Old tokens are blacklisted after rotation

### 2. Permission System
- **Owner-Only Access**: Users can only access their own data
- **Staff Override**: Staff users can access all data
- **OIDC Verification**: Ensures users are authenticated via OIDC
- **Granular Permissions**: Different permission levels for different endpoints

### 3. Data Protection
- **HTTPS Required**: All authentication should use HTTPS in production
- **Secure Headers**: CSRF protection and secure headers
- **Session Management**: Secure session handling
- **Input Validation**: Comprehensive input validation

## Testing

### Running Authentication Tests

```bash
# Run all authentication tests
docker-compose exec web pytest catalog/tests/test_auth.py -v

# Run specific test class
docker-compose exec web pytest catalog/tests/test_auth.py::OIDCAuthenticationTestCase -v

# Run with coverage
docker-compose exec web pytest catalog/tests/test_auth.py --cov=catalog.auth_backends --cov=catalog.permissions
```

### Test Categories

1. **OIDCAuthenticationTestCase**: OIDC user creation and updates
2. **JWTAuthenticationTestCase**: JWT token generation and validation
3. **PermissionTestCase**: API permission enforcement
4. **OrderAuthenticationTestCase**: Order-specific authentication
5. **CustomerProfileAuthenticationTestCase**: Profile-specific authentication
6. **MockOIDCTestCase**: Mocked OIDC for local testing

### Mocking OIDC for Local Testing

```python
from unittest.mock import patch

# Mock OIDC authentication
with patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True):
    # Your test code here
    response = client.get('/api/v1/orders/')
    assert response.status_code == 200
```

## Production Deployment

### 1. OIDC Provider Setup

Configure your OIDC provider (e.g., Auth0, Keycloak, Azure AD):

1. **Create Application**: Register TechMart API as an OIDC client
2. **Configure Redirect URIs**: Add your callback URL
3. **Set Scopes**: Configure required scopes (openid, email, profile)
4. **Get Credentials**: Obtain client ID and secret

### 2. Environment Configuration

```env
# Production OIDC Configuration
OIDC_RP_CLIENT_ID=your-production-client-id
OIDC_RP_CLIENT_SECRET=your-production-client-secret
OIDC_OP_AUTHORIZATION_ENDPOINT=https://your-oidc-provider.com/auth
OIDC_OP_TOKEN_ENDPOINT=https://your-oidc-provider.com/token
OIDC_OP_USER_ENDPOINT=https://your-oidc-provider.com/userinfo
OIDC_OP_JWKS_ENDPOINT=https://your-oidc-provider.com/.well-known/jwks.json
```

### 3. Security Considerations

- **HTTPS Only**: Use HTTPS for all authentication endpoints
- **Secure Secrets**: Store OIDC secrets securely (e.g., AWS Secrets Manager)
- **Token Validation**: Validate all tokens server-side
- **Rate Limiting**: Implement rate limiting on authentication endpoints
- **Monitoring**: Monitor authentication failures and suspicious activity

## Troubleshooting

### Common Issues

1. **OIDC Provider Not Found**
   - Check OIDC endpoint URLs
   - Verify network connectivity
   - Check OIDC provider status

2. **Token Validation Failed**
   - Check JWT signing algorithm
   - Verify token expiration
   - Check token format

3. **Permission Denied**
   - Verify user authentication status
   - Check OIDC authentication requirement
   - Verify user permissions

### Debug Mode

Enable debug logging for authentication:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'mozilla_django_oidc': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'rest_framework_simplejwt': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## API Documentation

- **Swagger UI**: http://localhost:8001/api/docs/
- **ReDoc**: http://localhost:8001/api/redoc/
- **OpenAPI Schema**: http://localhost:8001/api/schema/

The API documentation includes authentication requirements for each endpoint and provides interactive testing capabilities.
