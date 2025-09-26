from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import logging
from .models import CustomerProfile

logger = logging.getLogger(__name__)


class TechMartOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """Enhanced OIDC authentication backend for TechMart API."""
    
    def create_user(self, claims):
        """Create a new user from OIDC claims with enhanced error handling."""
        try:
            # Validate required claims
            if not self._validate_claims(claims):
                logger.error("Invalid claims provided for user creation")
                raise ValidationError("Invalid claims provided")
            
            # Create user with enhanced validation and proper field mapping
            user = self.UserModel.objects.create_user(
                username=claims.get('sub'),
                email=claims.get('email', ''),
                first_name=claims.get('given_name', ''),
                last_name=claims.get('family_name', ''),
            )
            
            # Create customer profile with enhanced data
            self._create_customer_profile(user, claims)
            
            logger.info(f"Successfully created user {user.username} via OIDC")
            return user
            
        except Exception as e:
            logger.error(f"Failed to create user via OIDC: {str(e)}")
            raise ValidationError(f"User creation failed: {str(e)}")
    
    def _create_customer_profile(self, user, claims):
        """Create customer profile with enhanced data mapping."""
        try:
            # Enhanced claims mapping
            profile_data = {
                'user': user,
                'phone': self._extract_phone(claims),
                'address': self._extract_address(claims),
            }
            
            CustomerProfile.objects.create(**profile_data)
            logger.info(f"Created customer profile for user {user.username}")
            
        except Exception as e:
            logger.error(f"Failed to create customer profile for {user.username}: {str(e)}")
            # Don't fail user creation if profile creation fails
            pass
    
    def _extract_phone(self, claims):
        """Extract phone number from claims with fallback options."""
        # Try multiple possible claim names for phone
        phone_claims = ['phone_number', 'phone', 'mobile', 'telephone']
        for claim in phone_claims:
            phone = claims.get(claim, '').strip()
            if phone:
                return phone
        return ''
    
    def _extract_address(self, claims):
        """Extract address from claims with fallback options."""
        # Try multiple possible claim names for address
        address_claims = ['address', 'street_address', 'location', 'home_address']
        for claim in address_claims:
            address = claims.get(claim, '').strip()
            if address:
                return address
        return ''
    
    def _validate_claims(self, claims):
        """Enhanced claims validation."""
        required_claims = ['email', 'sub']
        
        # Check required claims
        for claim in required_claims:
            if not claims.get(claim):
                logger.warning(f"Missing required claim: {claim}")
                return False
        
        # Validate email format
        email = claims.get('email', '')
        if email and '@' not in email:
            logger.warning(f"Invalid email format: {email}")
            return False
        
        return True
    
    def update_user(self, user, claims):
        """Update existing user with OIDC claims with enhanced error handling."""
        try:
            # Validate claims before updating
            if not self._validate_claims(claims):
                logger.warning(f"Invalid claims provided for user update: {user.username}")
                return user
            
            # Update user fields with proper mapping
            user.email = claims.get('email', user.email)
            user.first_name = claims.get('given_name', user.first_name)
            user.last_name = claims.get('family_name', user.last_name)
            user.save()
            
            # Update customer profile with enhanced data
            self._update_customer_profile(user, claims)
            
            logger.info(f"Successfully updated user {user.username} via OIDC")
            return user
            
        except Exception as e:
            logger.error(f"Failed to update user {user.username} via OIDC: {str(e)}")
            return user
    
    def _update_customer_profile(self, user, claims):
        """Update customer profile with enhanced data mapping."""
        try:
            profile = user.profile
            
            # Update profile with enhanced data extraction
            new_phone = self._extract_phone(claims)
            new_address = self._extract_address(claims)
            
            # Only update if new data is provided and different
            if new_phone and new_phone != profile.phone:
                profile.phone = new_phone
                logger.info(f"Updated phone for user {user.username}")
            
            if new_address and new_address != profile.address:
                profile.address = new_address
                logger.info(f"Updated address for user {user.username}")
            
            profile.save()
            
        except CustomerProfile.DoesNotExist:
            # Create profile if it doesn't exist
            logger.info(f"Creating missing profile for user {user.username}")
            self._create_customer_profile(user, claims)
        except Exception as e:
            logger.error(f"Failed to update customer profile for {user.username}: {str(e)}")
            # Don't fail user update if profile update fails
            pass
    
    def filter_users_by_claims(self, claims):
        """Filter users by OIDC claims with enhanced error handling."""
        try:
            email = claims.get('email')
            if not email:
                logger.warning("No email provided in claims for user filtering")
                return self.UserModel.objects.none()
            
            # Enhanced user filtering with logging
            users = self.UserModel.objects.filter(email__iexact=email)
            logger.info(f"Found {users.count()} users with email {email}")
            return users
            
        except Exception as e:
            logger.error(f"Error filtering users by claims: {str(e)}")
            return self.UserModel.objects.none()
    
    def verify_claims(self, claims):
        """Enhanced claims verification with detailed logging."""
        try:
            # Check for required claims
            required_claims = ['email', 'sub']
            missing_claims = [claim for claim in required_claims if not claims.get(claim)]
            
            if missing_claims:
                logger.warning(f"Missing required claims: {missing_claims}")
                return False
            
            # Additional validation
            if not self._validate_claims(claims):
                logger.warning("Claims validation failed")
                return False
            
            logger.info("Claims verification successful")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying claims: {str(e)}")
            return False
