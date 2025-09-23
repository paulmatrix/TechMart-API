from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import User
from .models import CustomerProfile


class TechMartOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """Custom OIDC authentication backend for TechMart API."""
    
    def create_user(self, claims):
        """Create a new user from OIDC claims."""
        user = super().create_user(claims)
        
        # Create customer profile
        CustomerProfile.objects.create(
            user=user,
            phone=claims.get('phone_number', ''),
            address=claims.get('address', '')
        )
        
        return user
    
    def update_user(self, user, claims):
        """Update existing user with OIDC claims."""
        user = super().update_user(user, claims)
        
        # Update customer profile if it exists
        try:
            profile = user.profile
            profile.phone = claims.get('phone_number', profile.phone)
            profile.address = claims.get('address', profile.address)
            profile.save()
        except CustomerProfile.DoesNotExist:
            # Create profile if it doesn't exist
            CustomerProfile.objects.create(
                user=user,
                phone=claims.get('phone_number', ''),
                address=claims.get('address', '')
            )
        
        return user
    
    def filter_users_by_claims(self, claims):
        """Filter users by OIDC claims."""
        email = claims.get('email')
        if not email:
            return self.UserModel.objects.none()
        
        try:
            return self.UserModel.objects.filter(email__iexact=email)
        except self.UserModel.DoesNotExist:
            return self.UserModel.objects.none()
    
    def verify_claims(self, claims):
        """Verify that the claims are valid."""
        # Check for required claims
        required_claims = ['email', 'sub']
        return all(claim in claims for claim in required_claims)
