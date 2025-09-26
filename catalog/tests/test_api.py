import pytest
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import CustomerProfile, Category, Product, Order, OrderItem


class BaseAPITestCase(APITestCase):
    """Base test case with common setup."""
    
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
        
        # Create customer profiles
        self.customer_profile = CustomerProfile.objects.create(
            user=self.user,
            phone='+1234567890',
            address='123 Test Street, Test City'
        )
        
        # Create categories
        self.electronics = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic devices and gadgets'
        )
        self.phones = Category.objects.create(
            name='Phones',
            slug='phones',
            description='Mobile phones and accessories',
            parent=self.electronics
        )
        self.smartphones = Category.objects.create(
            name='Smartphones',
            slug='smartphones',
            description='Smart mobile phones',
            parent=self.phones
        )
        
        # Create products
        self.iphone = Product.objects.create(
            name='iPhone 15',
            sku='IPH15-128',
            description='Latest iPhone model',
            category=self.smartphones,
            price=Decimal('999.99'),
            stock_quantity=10
        )
        self.samsung = Product.objects.create(
            name='Samsung Galaxy S24',
            sku='SGS24-256',
            description='Latest Samsung flagship',
            category=self.smartphones,
            price=Decimal('899.99'),
            stock_quantity=5
        )
        self.laptop = Product.objects.create(
            name='MacBook Pro',
            sku='MBP-14',
            description='Apple MacBook Pro 14-inch',
            category=self.electronics,
            price=Decimal('1999.99'),
            stock_quantity=3
        )
        
        # Create API client and authenticate
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)


class CategoryAPITestCase(BaseAPITestCase):
    """Test cases for Category API endpoints."""
    
    def test_list_categories(self):
        """Test listing categories."""
        url = reverse('catalog:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_create_category(self):
        """Test creating a new category."""
        url = reverse('catalog:category-list')
        data = {
            'name': 'Tablets',
            'description': 'Tablet devices',
            'parent': self.electronics.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 4)
        self.assertEqual(response.data['name'], 'Tablets')
    
    def test_category_hierarchy(self):
        """Test category hierarchy structure."""
        url = reverse('catalog:category-detail', kwargs={'id': self.electronics.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['children']), 1)  # Phones
        self.assertEqual(response.data['children'][0]['name'], 'Phones')
    
    def test_category_average_price(self):
        """Test category average price calculation."""
        url = reverse('catalog:category-average-price', kwargs={'id': self.electronics.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('average_price', response.data)
        self.assertIn('product_count', response.data)
        self.assertIn('descendant_categories', response.data)
        
        # Should include all products in Electronics and its descendants
        expected_avg = (Decimal('999.99') + Decimal('899.99') + Decimal('1999.99')) / 3
        self.assertAlmostEqual(
            float(response.data['average_price']),
            float(expected_avg),
            places=2
        )
    
    def test_category_tree(self):
        """Test category tree endpoint."""
        url = reverse('catalog:category-tree')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only Electronics (root category)
        self.assertEqual(response.data[0]['name'], 'Electronics')


class ProductAPITestCase(BaseAPITestCase):
    """Test cases for Product API endpoints."""
    
    def test_list_products(self):
        """Test listing products."""
        url = reverse('catalog:product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_create_product(self):
        """Test creating a new product."""
        url = reverse('catalog:product-list')
        data = {
            'name': 'iPad Pro',
            'sku': 'IPAD-PRO-12',
            'description': 'Apple iPad Pro 12.9-inch',
            'category': self.electronics.id,
            'price': '1099.99',
            'stock_quantity': 8
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 4)
        self.assertEqual(response.data['name'], 'iPad Pro')
    
    def test_product_filters(self):
        """Test product filtering."""
        # Filter by category
        url = reverse('catalog:product-list')
        response = self.client.get(url, {'category': self.smartphones.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # iPhone and Samsung
        
        # Filter by price range
        response = self.client.get(url, {'min_price': '900', 'max_price': '1000'})
        self.assertEqual(len(response.data['results']), 1)  # Only iPhone
        
        # Filter by stock status
        response = self.client.get(url, {'in_stock': 'true'})
        self.assertEqual(len(response.data['results']), 3)  # All products are in stock
    
    def test_add_stock(self):
        """Test adding stock to a product."""
        url = reverse('catalog:product-add-stock', kwargs={'pk': self.iphone.id})
        data = {'quantity': 5}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.iphone.refresh_from_db()
        self.assertEqual(self.iphone.stock_quantity, 15)
    
    def test_reduce_stock(self):
        """Test reducing stock from a product."""
        url = reverse('catalog:product-reduce-stock', kwargs={'pk': self.iphone.id})
        data = {'quantity': 3}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.iphone.refresh_from_db()
        self.assertEqual(self.iphone.stock_quantity, 7)
    
    def test_reduce_stock_insufficient(self):
        """Test reducing stock when insufficient."""
        url = reverse('catalog:product-reduce-stock', kwargs={'pk': self.iphone.id})
        data = {'quantity': 20}  # More than available
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', response.data['error'])


class OrderAPITestCase(BaseAPITestCase):
    """Test cases for Order API endpoints."""
    
    @patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True)
    def test_create_order(self, mock_oidc):
        """Test creating an order with items."""
        url = reverse('catalog:order-list')
        data = {
            'items': [
                {'product': self.iphone.id, 'quantity': 2},
                {'product': self.samsung.id, 'quantity': 1}
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        
        order = Order.objects.first()
        self.assertEqual(order.customer, self.user)
        self.assertEqual(order.items.count(), 2)
        
        # Check total calculation
        expected_total = (Decimal('999.99') * 2) + (Decimal('899.99') * 1)
        self.assertEqual(order.total, expected_total)
    
    def test_order_total_calculation(self):
        """Test order total calculation with multiple items."""
        order = Order.objects.create(customer=self.user)
        
        # Create order items
        OrderItem.objects.create(
            order=order,
            product=self.iphone,
            quantity=2,
            purchase_price=self.iphone.price
        )
        OrderItem.objects.create(
            order=order,
            product=self.laptop,
            quantity=1,
            purchase_price=self.laptop.price
        )
        
        # Calculate total
        order.calculate_total()
        
        expected_total = (Decimal('999.99') * 2) + (Decimal('1999.99') * 1)
        self.assertEqual(order.total, expected_total)
    
    @patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True)
    def test_order_stock_reduction(self, mock_oidc):
        """Test that stock is reduced when order is created."""
        initial_iphone_stock = self.iphone.stock_quantity
        initial_samsung_stock = self.samsung.stock_quantity
        
        url = reverse('catalog:order-list')
        data = {
            'items': [
                {'product': self.iphone.id, 'quantity': 3},
                {'product': self.samsung.id, 'quantity': 2}
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check stock reduction
        self.iphone.refresh_from_db()
        self.samsung.refresh_from_db()
        
        self.assertEqual(self.iphone.stock_quantity, initial_iphone_stock - 3)
        self.assertEqual(self.samsung.stock_quantity, initial_samsung_stock - 2)
    
    @patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True)
    def test_order_cancel(self, mock_oidc):
        """Test order cancellation and stock restoration."""
        # Create an order
        order = Order.objects.create(customer=self.user)
        OrderItem.objects.create(
            order=order,
            product=self.iphone,
            quantity=2,
            purchase_price=self.iphone.price
        )
        
        initial_stock = self.iphone.stock_quantity
        
        # Reduce stock
        self.iphone.reduce_stock(2)
        
        # Cancel order
        url = reverse('catalog:order-cancel', kwargs={'pk': order.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check stock restoration
        self.iphone.refresh_from_db()
        self.assertEqual(self.iphone.stock_quantity, initial_stock)
        
        # Check order status
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')
    
    @patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True)
    def test_order_insufficient_stock(self, mock_oidc):
        """Test order creation with insufficient stock."""
        url = reverse('catalog:order-list')
        data = {
            'items': [
                {'product': self.iphone.id, 'quantity': 20}  # More than available
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exceeds available stock', str(response.data))
    
    @patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True)
    def test_order_duplicate_products(self, mock_oidc):
        """Test order creation with duplicate products."""
        url = reverse('catalog:order-list')
        data = {
            'items': [
                {'product': self.iphone.id, 'quantity': 1},
                {'product': self.iphone.id, 'quantity': 2}  # Duplicate product
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Duplicate products', str(response.data))


class SerializerValidationTestCase(BaseAPITestCase):
    """Test cases for serializer validation."""
    
    def test_product_price_validation(self):
        """Test product price validation."""
        url = reverse('catalog:product-list')
        data = {
            'name': 'Test Product',
            'sku': 'TEST-001',
            'category': self.electronics.id,
            'price': '-10.00',  # Negative price
            'stock_quantity': 5
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Ensure this value is greater than or equal to 0.01', str(response.data))
    
    @patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True)
    def test_order_item_quantity_validation(self, mock_oidc):
        """Test order item quantity validation."""
        url = reverse('catalog:order-list')
        data = {
            'items': [
                {'product': self.iphone.id, 'quantity': 0}  # Invalid quantity
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Ensure this value is greater than or equal to 1', str(response.data))
    
    @patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True)
    def test_empty_order_validation(self, mock_oidc):
        """Test order creation with no items."""
        url = reverse('catalog:order-list')
        data = {'items': []}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Order must have at least one item', str(response.data))


class AuthenticationTestCase(BaseAPITestCase):
    """Test cases for authentication and permissions."""
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access protected endpoints."""
        self.client.credentials()  # Remove authentication
        
        url = reverse('catalog:order-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_orders_filtering(self):
        """Test that users can only see their own orders."""
        # Create another user and order
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_order = Order.objects.create(customer=other_user)
        
        # Test that current user can only see their own orders
        url = reverse('catalog:order-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)  # No orders for current user yet
    
    def test_staff_user_access(self):
        """Test that staff users can access all orders."""
        # Create staff token
        staff_refresh = RefreshToken.for_user(self.staff_user)
        staff_access_token = str(staff_refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + staff_access_token)
        
        # Create order for regular user
        order = Order.objects.create(customer=self.user)
        
        url = reverse('catalog:order-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
