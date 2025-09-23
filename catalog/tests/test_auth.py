import pytest
import json
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import CustomerProfile, Category, Product, Order, OrderItem


class BaseAuthTestCase(APITestCase):
    """Base test case for authentication tests."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        # Create customer profiles (simulating OIDC users)
        self.customer_profile = CustomerProfile.objects.create(
            user=self.user,
            phone='+1234567890',
            address='123 Test Street, Test City'
        )
        self.staff_profile = CustomerProfile.objects.create(
            user=self.staff_user,
            phone='+1234567891',
            address='456 Staff Street, Staff City'
        )
        
        # Create test data
        self.electronics = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic devices'
        )
        self.iphone = Product.objects.create(
            name='iPhone 15',
            sku='IPH15-128',
            description='Latest iPhone',
            category=self.electronics,
            price=Decimal('999.99'),
            stock_quantity=10
        )
        
        # Create API client
        self.client = APIClient()


class OIDCAuthenticationTestCase(BaseAuthTestCase):
    """Test cases for OIDC authentication."""
    
    def test_oidc_user_creation(self):
        """Test that OIDC users are created with profiles."""
        # Simulate OIDC claims
        claims = {
            'sub': 'oidc-user-123',
            'email': 'oidc@example.com',
            'given_name': 'OIDC',
            'family_name': 'User',
            'phone_number': '+1234567892',
            'address': '789 OIDC Street, OIDC City'
        }
        
        # Mock OIDC authentication
        with patch('catalog.auth_backends.TechMartOIDCAuthenticationBackend.verify_claims', return_value=True):
            with patch('catalog.auth_backends.TechMartOIDCAuthenticationBackend.filter_users_by_claims', return_value=User.objects.none()):
                backend = __import__('catalog.auth_backends', fromlist=['TechMartOIDCAuthenticationBackend']).TechMartOIDCAuthenticationBackend()
                
                # Create user
                user = backend.create_user(claims)
                
                # Verify user was created
                self.assertIsNotNone(user)
                self.assertEqual(user.email, 'oidc@example.com')
                self.assertEqual(user.first_name, 'OIDC')
                self.assertEqual(user.last_name, 'User')
                
                # Verify profile was created
                profile = user.profile
                self.assertEqual(profile.phone, '+1234567892')
                self.assertEqual(profile.address, '789 OIDC Street, OIDC City')
    
    def test_oidc_user_update(self):
        """Test that OIDC users are updated with new claims."""
        claims = {
            'sub': 'oidc-user-123',
            'email': 'updated@example.com',
            'given_name': 'Updated',
            'family_name': 'User',
            'phone_number': '+1234567893',
            'address': 'Updated Address'
        }
        
        with patch('catalog.auth_backends.TechMartOIDCAuthenticationBackend.verify_claims', return_value=True):
            with patch('catalog.auth_backends.TechMartOIDCAuthenticationBackend.filter_users_by_claims', return_value=User.objects.filter(id=self.user.id)):
                backend = __import__('catalog.auth_backends', fromlist=['TechMartOIDCAuthenticationBackend']).TechMartOIDCAuthenticationBackend()
                
                # Update user
                updated_user = backend.update_user(self.user, claims)
                
                # Verify user was updated
                self.assertEqual(updated_user.email, 'updated@example.com')
                self.assertEqual(updated_user.first_name, 'Updated')
                self.assertEqual(updated_user.last_name, 'User')
                
                # Verify profile was updated
                profile = updated_user.profile
                self.assertEqual(profile.phone, '+1234567893')
                self.assertEqual(profile.address, 'Updated Address')


class JWTAuthenticationTestCase(BaseAuthTestCase):
    """Test cases for JWT authentication."""
    
    def test_jwt_token_obtain(self):
        """Test JWT token obtain endpoint."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_jwt_token_refresh(self):
        """Test JWT token refresh endpoint."""
        # Get refresh token
        refresh = RefreshToken.for_user(self.user)
        
        url = reverse('token_refresh')
        data = {'refresh': str(refresh)}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_jwt_authenticated_request(self):
        """Test authenticated request with JWT token."""
        # Get access token
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        # Make authenticated request
        url = reverse('catalog:order-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PermissionTestCase(BaseAuthTestCase):
    """Test cases for API permissions."""
    
    def test_public_read_access_categories(self):
        """Test that categories are publicly readable."""
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_public_read_access_products(self):
        """Test that products are publicly readable."""
        url = reverse('catalog:product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_authenticated_write_access_categories(self):
        """Test that category creation requires authentication."""
        url = reverse('catalog:category-list')
        data = {
            'name': 'Test Category',
            'description': 'Test Description'
        }
        
        # Unauthenticated request should fail
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Authenticated request should succeed
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_authenticated_write_access_products(self):
        """Test that product creation requires authentication."""
        url = reverse('catalog:product-list')
        data = {
            'name': 'Test Product',
            'sku': 'TEST-001',
            'description': 'Test Product Description',
            'category': self.electronics.id,
            'price': '99.99',
            'stock_quantity': 5
        }
        
        # Unauthenticated request should fail
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Authenticated request should succeed
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_oidc_required_for_orders(self):
        """Test that orders require OIDC authentication."""
        url = reverse('catalog:order-list')
        
        # Unauthenticated request should fail
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Regular JWT authentication should fail (not OIDC)
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_oidc_required_for_customer_profiles(self):
        """Test that customer profiles require OIDC authentication."""
        url = reverse('catalog:customerprofile-list')
        
        # Unauthenticated request should fail
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Regular JWT authentication should fail (not OIDC)
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OrderAuthenticationTestCase(BaseAuthTestCase):
    """Test cases for order authentication and authorization."""
    
    def test_order_creation_requires_oidc(self):
        """Test that order creation requires OIDC authentication."""
        url = reverse('catalog:order-list')
        data = {
            'items': [
                {'product': self.iphone.id, 'quantity': 1}
            ]
        }
        
        # Unauthenticated request should fail
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Regular JWT authentication should fail
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_order_access_owner_only(self):
        """Test that users can only access their own orders."""
        # Create order for user
        order = Order.objects.create(customer=self.user)
        OrderItem.objects.create(
            order=order,
            product=self.iphone,
            quantity=1,
            purchase_price=self.iphone.price
        )
        
        # Create another user and order
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_order = Order.objects.create(customer=other_user)
        
        # Mock OIDC authentication for user
        with patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True):
            refresh = RefreshToken.for_user(self.user)
            access_token = str(refresh.access_token)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            url = reverse('catalog:order-list')
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Should only see user's own order
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['id'], order.id)
    
    def test_staff_access_all_orders(self):
        """Test that staff users can access all orders."""
        # Create orders for different users
        order1 = Order.objects.create(customer=self.user)
        order2 = Order.objects.create(customer=self.staff_user)
        
        # Mock OIDC authentication for staff user
        with patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True):
            refresh = RefreshToken.for_user(self.staff_user)
            access_token = str(refresh.access_token)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            url = reverse('catalog:order-list')
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Should see all orders
            self.assertEqual(len(response.data['results']), 2)


class CustomerProfileAuthenticationTestCase(BaseAuthTestCase):
    """Test cases for customer profile authentication and authorization."""
    
    def test_profile_access_owner_only(self):
        """Test that users can only access their own profile."""
        # Mock OIDC authentication
        with patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True):
            refresh = RefreshToken.for_user(self.user)
            access_token = str(refresh.access_token)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            # Access own profile should succeed
            url = reverse('catalog:customerprofile-detail', kwargs={'id': self.customer_profile.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Access other user's profile should fail
            url = reverse('catalog:customerprofile-detail', kwargs={'id': self.staff_profile.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_staff_access_all_profiles(self):
        """Test that staff users can access all profiles."""
        # Mock OIDC authentication for staff user
        with patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True):
            refresh = RefreshToken.for_user(self.staff_user)
            access_token = str(refresh.access_token)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            # Access any profile should succeed
            url = reverse('catalog:customerprofile-detail', kwargs={'id': self.customer_profile.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            url = reverse('catalog:customerprofile-detail', kwargs={'id': self.staff_profile.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class MockOIDCTestCase(BaseAuthTestCase):
    """Test cases using mocked OIDC authentication for local testing."""
    
    def setUp(self):
        super().setUp()
        # Mock OIDC authentication for all tests in this class
        self.oidc_patcher = patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True)
        self.oidc_patcher.start()
    
    def tearDown(self):
        self.oidc_patcher.stop()
    
    def test_mocked_oidc_order_creation(self):
        """Test order creation with mocked OIDC authentication."""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        url = reverse('catalog:order-list')
        data = {
            'items': [
                {'product': self.iphone.id, 'quantity': 2}
            ]
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify order was created
        order = Order.objects.get(id=response.data['id'])
        self.assertEqual(order.customer, self.user)
        self.assertEqual(order.items.count(), 1)
    
    def test_mocked_oidc_profile_access(self):
        """Test profile access with mocked OIDC authentication."""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        url = reverse('catalog:customerprofile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.customer_profile.id)
