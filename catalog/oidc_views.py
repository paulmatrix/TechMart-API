"""
Custom OIDC Views for Enhanced User Experience
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from mozilla_django_oidc.views import OIDCAuthenticationRequestView, OIDCAuthenticationCallbackView, OIDCLogoutView
from mozilla_django_oidc.utils import import_from_settings
import logging

logger = logging.getLogger(__name__)


class TechMartOIDCLoginView(OIDCAuthenticationRequestView):
    """Enhanced OIDC login view with better error handling and UX."""
    
    def get(self, request):
        """Handle OIDC login initiation with enhanced error handling."""
        try:
            # Log login attempt
            logger.info(f"OIDC login initiated for user: {request.user if request.user.is_authenticated else 'Anonymous'}")
            
            # Call parent method
            response = super().get(request)
            
            # Log successful initiation
            logger.info("OIDC login initiation successful")
            return response
            
        except Exception as e:
            logger.error(f"OIDC login initiation failed: {str(e)}")
            messages.error(request, "Login failed. Please try again.")
            return redirect('/api/docs/')
    
    def post(self, request):
        """Handle POST requests for OIDC login."""
        return self.get(request)


class TechMartOIDCCallbackView(OIDCAuthenticationCallbackView):
    """Enhanced OIDC callback view with better error handling and user feedback."""
    
    def get(self, request):
        """Handle OIDC callback with enhanced error handling."""
        try:
            # Log callback attempt
            logger.info("OIDC callback received")
            
            # Call parent method
            response = super().get(request)
            
            # Check if authentication was successful
            if request.user.is_authenticated:
                logger.info(f"OIDC authentication successful for user: {request.user.username}")
                messages.success(request, f"Welcome back, {request.user.first_name or request.user.username}!")
                
                # Get the authorization code from the request
                auth_code = request.GET.get('code')
                state = request.GET.get('state')
                
                if auth_code:
                    # Create a simple page showing the code for easy copying
                    return render(request, 'catalog/oidc_success.html', {
                        'auth_code': auth_code,
                        'state': state,
                        'user': request.user
                    })
                
                # Redirect to API documentation page
                return redirect('/api/docs/')
            else:
                logger.warning("OIDC authentication failed - user not authenticated")
                messages.error(request, "Authentication failed. Please try again.")
                return redirect('/api/docs/')
                
        except Exception as e:
            logger.error(f"OIDC callback failed: {str(e)}")
            messages.error(request, "Authentication failed. Please try again.")
            return redirect('/api/docs/')
    
    def post(self, request):
        """Handle POST requests for OIDC callback."""
        return self.get(request)


class TechMartOIDCLogoutView(OIDCLogoutView):
    """Enhanced OIDC logout view with better user feedback."""
    
    def get(self, request):
        """Handle OIDC logout with enhanced error handling."""
        try:
            # Log logout attempt
            if request.user.is_authenticated:
                logger.info(f"OIDC logout initiated for user: {request.user.username}")
            
            # Call parent method
            response = super().get(request)
            
            # Add success message
            messages.success(request, "You have been successfully logged out.")
            
            logger.info("OIDC logout successful")
            return response
            
        except Exception as e:
            logger.error(f"OIDC logout failed: {str(e)}")
            messages.error(request, "Logout failed. Please try again.")
            return redirect('/api/docs/')


class OIDCStatusView(View):
    """View to check OIDC authentication status."""
    
    def get(self, request):
        """Return OIDC authentication status."""
        try:
            if request.user.is_authenticated:
                # Get user profile if available
                profile_data = {}
                if hasattr(request.user, 'profile'):
                    profile = request.user.profile
                    profile_data = {
                        'phone': profile.phone,
                        'address': profile.address,
                    }
                
                return JsonResponse({
                    'authenticated': True,
                    'user': {
                        'id': request.user.id,
                        'username': request.user.username,
                        'email': request.user.email,
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name,
                        'profile': profile_data,
                    }
                })
            else:
                return JsonResponse({
                    'authenticated': False,
                    'user': None
                })
                
        except Exception as e:
            logger.error(f"Error checking OIDC status: {str(e)}")
            return JsonResponse({
                'error': 'Failed to check authentication status'
            }, status=500)


class OIDCErrorView(View):
    """View to handle OIDC errors with user-friendly messages."""
    
    def get(self, request):
        """Display OIDC error page."""
        error_code = request.GET.get('error', 'unknown')
        error_description = request.GET.get('error_description', 'An unknown error occurred')
        
        # Log the error
        logger.error(f"OIDC error: {error_code} - {error_description}")
        
        # Map error codes to user-friendly messages
        error_messages = {
            'access_denied': 'Access was denied. Please try again.',
            'invalid_request': 'Invalid request. Please try again.',
            'unauthorized_client': 'Authentication failed. Please try again.',
            'unsupported_response_type': 'Authentication failed. Please try again.',
            'invalid_scope': 'Authentication failed. Please try again.',
            'server_error': 'Server error. Please try again later.',
            'temporarily_unavailable': 'Service temporarily unavailable. Please try again later.',
        }
        
        user_message = error_messages.get(error_code, 'Authentication failed. Please try again.')
        
        context = {
            'error_code': error_code,
            'error_description': error_description,
            'user_message': user_message,
        }
        
        return render(request, 'catalog/oidc_error.html', context)


# API Views for OIDC
class OIDCLoginAPIView(View):
    """API view for OIDC login initiation."""
    
    def get(self, request):
        """Return OIDC login URL for API clients."""
        try:
            # Get OIDC settings
            oidc_settings = import_from_settings('OIDC_RP_CLIENT_ID')
            
            # Construct login URL
            login_url = f"/oidc/authenticate/"
            
            return JsonResponse({
                'login_url': login_url,
                'message': 'Use this URL to initiate OIDC login'
            })
            
        except Exception as e:
            logger.error(f"Error generating OIDC login URL: {str(e)}")
            return JsonResponse({
                'error': 'Failed to generate login URL'
            }, status=500)


class OIDCLogoutAPIView(View):
    """API view for OIDC logout."""
    
    def post(self, request):
        """Handle OIDC logout via API."""
        try:
            if request.user.is_authenticated:
                logger.info(f"OIDC logout via API for user: {request.user.username}")
                
                # Logout user
                from django.contrib.auth import logout
                logout(request)
                
                return JsonResponse({
                    'message': 'Successfully logged out',
                    'logout_url': '/oidc/logout/'
                })
            else:
                return JsonResponse({
                    'message': 'User not authenticated'
                }, status=400)
                
        except Exception as e:
            logger.error(f"Error during OIDC logout via API: {str(e)}")
            return JsonResponse({
                'error': 'Failed to logout'
            }, status=500)
