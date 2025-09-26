from rest_framework import permissions


class IsAuthenticatedOrReadOnlyForStaff(permissions.BasePermission):
    """
    Custom permission to allow:
    - Read access for everyone
    - Write access only for authenticated users
    - Full access for staff users
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed for authenticated users
        return request.user and request.user.is_authenticated


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to allow:
    - Users to access their own data
    - Staff users to access all data
    """
    
    def has_object_permission(self, request, view, obj):
        # Staff users have full access
        if request.user.is_staff:
            return True
        
        # Users can only access their own data
        if hasattr(obj, 'customer'):
            return obj.customer == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsOIDCAuthenticated(permissions.BasePermission):
    """
    Custom permission to require OIDC authentication.
    This ensures that only users authenticated via OIDC can access the endpoint.
    Staff users are exempt from this requirement.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff users can always access (bypass OIDC requirement)
        if request.user.is_staff:
            return True
        
        # Check if user was created via OIDC (has a profile)
        try:
            request.user.profile
            return True
        except:
            return False


class IsOIDCAuthenticatedOrStaff(permissions.BasePermission):
    """
    Custom permission that allows:
    - Staff users (regardless of authentication method)
    - OIDC authenticated users (with profiles)
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff users can always access
        if request.user.is_staff:
            return True
        
        # Check if user was created via OIDC (has a profile)
        try:
            request.user.profile
            return True
        except:
            return False
