from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerProfileViewSet, CategoryViewSet, ProductViewSet, OrderViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'customer-profiles', CustomerProfileViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)

app_name = 'catalog'

urlpatterns = [
    path('', include(router.urls)),
]
