from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerProfileViewSet, CategoryViewSet, ProductViewSet, OrderViewSet
)
from .oidc_auth_views import oidc_token_exchange, oidc_refresh_token, oidc_auth_url

# Create router and register viewsets
router = DefaultRouter()
router.register(r'customer-profiles', CustomerProfileViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)

app_name = 'catalog'

urlpatterns = [
    path('', include(router.urls)),
    
    # OIDC Authentication endpoints
    path('oidc/token/', oidc_token_exchange, name='oidc-token-exchange'),
    path('oidc/refresh/', oidc_refresh_token, name='oidc-refresh-token'),
    path('oidc/auth-url/', oidc_auth_url, name='oidc-auth-url'),
]
