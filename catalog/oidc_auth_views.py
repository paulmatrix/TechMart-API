"""
Custom OIDC authentication views for generating JWT tokens.
"""

import logging
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.utils import import_from_settings
import json

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def oidc_token_exchange(request):
    """
    Exchange OIDC authorization code for JWT tokens.
    
    This endpoint allows OIDC users to get JWT tokens for API access
    after they've completed the OIDC authentication flow.
    
    POST /api/v1/oidc/token/
    Body: {
        "authorization_code": "auth_code_from_oidc_callback",
        "state": "state_from_oidc_callback"
    }
    """
    try:
        authorization_code = request.data.get('authorization_code')
        state = request.data.get('state')
        
        if not authorization_code:
            return Response(
                {'error': 'Authorization code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Exchange authorization code for tokens
        from mozilla_django_oidc.utils import import_from_settings
        from mozilla_django_oidc.auth import OIDCAuthenticationBackend
        
        # Get OIDC settings
        client_id = import_from_settings('OIDC_RP_CLIENT_ID')
        client_secret = import_from_settings('OIDC_RP_CLIENT_SECRET')
        token_endpoint = import_from_settings('OIDC_OP_TOKEN_ENDPOINT')
        redirect_uri = import_from_settings('OIDC_RP_REDIRECT_URI')
        
        # Exchange code for tokens
        import requests
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret,
        }
        
        response = requests.post(token_endpoint, data=token_data)
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            return Response(
                {'error': 'Failed to exchange authorization code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token_response = response.json()
        access_token = token_response.get('access_token')
        id_token = token_response.get('id_token')
        
        if not access_token or not id_token:
            return Response(
                {'error': 'Invalid token response from OIDC provider'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user info from ID token
        from jose import jwt
        import json
        
        # Decode ID token (without verification for now)
        id_token_payload = jwt.get_unverified_claims(id_token)
        user_email = id_token_payload.get('email')
        
        if not user_email:
            return Response(
                {'error': 'No email found in ID token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find or create user
        from django.contrib.auth.models import User
        from catalog.models import CustomerProfile
        
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            # Create user automatically from OIDC claims
            logger.info(f"Creating new user for email: {user_email}")
            
            # Extract user info from ID token
            first_name = id_token_payload.get('given_name', '')
            last_name = id_token_payload.get('family_name', '')
            username = user_email  # Use email as username
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=user_email,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            # Create customer profile
            phone = id_token_payload.get('phone_number', '')
            address = id_token_payload.get('address', '')
            
            CustomerProfile.objects.create(
                user=user,
                phone=phone,
                address=address
            )
            
            logger.info(f"Successfully created user: {user.username}")
        
        # Generate JWT tokens for the user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })
        
    except Exception as e:
        logger.error(f"OIDC token exchange error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def oidc_refresh_token(request):
    """
    Refresh JWT tokens for OIDC users.
    
    POST /api/v1/oidc/refresh/
    Body: {
        "refresh": "refresh_token"
    }
    """
    try:
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify and refresh the token
        refresh = RefreshToken(refresh_token)
        new_access_token = refresh.access_token
        
        return Response({
            'access': str(new_access_token),
            'refresh': str(refresh),
        })
        
    except Exception as e:
        logger.error(f"OIDC token refresh error: {str(e)}")
        return Response(
            {'error': 'Invalid refresh token'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def oidc_auth_url(request):
    """
    Get the OIDC authentication URL for frontend applications.
    
    GET /api/v1/oidc/auth-url/
    """
    try:
        from mozilla_django_oidc.utils import import_from_settings
        
        client_id = import_from_settings('OIDC_RP_CLIENT_ID')
        redirect_uri = import_from_settings('OIDC_RP_REDIRECT_URI')
        scope = import_from_settings('OIDC_RP_SCOPES', 'openid email profile')
        
        # Generate state and nonce for security
        import secrets
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        
        # Store state and nonce in session for validation
        request.session['oidc_state'] = state
        request.session['oidc_nonce'] = nonce
        
        # Build authorization URL
        auth_url = f"https://dev-4clxla8b7lbloc3o.us.auth0.com/authorize"
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'state': state,
            'nonce': nonce,
        }
        
        # Add query parameters
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        full_auth_url = f"{auth_url}?{query_string}"
        
        return Response({
            'auth_url': full_auth_url,
            'state': state,
            'nonce': nonce,
        })
        
    except Exception as e:
        logger.error(f"OIDC auth URL generation error: {str(e)}")
        return Response(
            {'error': 'Failed to generate auth URL'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
