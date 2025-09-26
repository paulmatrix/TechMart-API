import pytest
from unittest.mock import patch, MagicMock, call
from decimal import Decimal
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import CustomerProfile, Category, Product, Order, OrderItem
from ..notifications import (
    send_order_sms, send_order_email, send_order_confirmation_email,
    send_order_status_update_sms, initialize_africastalking
)
from ..tasks import (
    send_order_sms_task, send_order_email_task, send_order_confirmation_email_task,
    send_order_status_update_sms_task, process_order_notifications
)


class BaseNotificationTestCase(APITestCase):
    """Base test case for notification tests."""
    
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


class NotificationFunctionTestCase(BaseNotificationTestCase):
    """Test cases for notification functions."""
    
    @patch('catalog.notifications.africastalking')
    def test_initialize_africastalking_success(self, mock_africastalking):
        """Test successful Africa's Talking initialization."""
        mock_sms = MagicMock()
        mock_africastalking.SMS.return_value = mock_sms
        
        result = initialize_africastalking()
        
        mock_africastalking.initialize.assert_called_once()
        mock_africastalking.SMS.assert_called_once()
        self.assertEqual(result, mock_sms)
    
    @patch('catalog.notifications.africastalking')
    def test_initialize_africastalking_failure(self, mock_africastalking):
        """Test Africa's Talking initialization failure."""
        mock_africastalking.initialize.side_effect = Exception("API Error")
        
        result = initialize_africastalking()
        
        self.assertIsNone(result)
    
    @patch('catalog.notifications.initialize_africastalking')
    def test_send_order_sms_success(self, mock_init):
        """Test successful SMS sending."""
        # Mock Africa's Talking SMS service
        mock_sms = MagicMock()
        mock_response = {
            'SMSMessageData': {
                'Recipients': [{'statusCode': 101}]
            }
        }
        mock_sms.send.return_value = mock_response
        mock_init.return_value = mock_sms
        
        result = send_order_sms('+1234567890', 1)
        
        self.assertTrue(result)
        mock_sms.send.assert_called_once()
    
    @patch('catalog.notifications.initialize_africastalking')
    def test_send_order_sms_failure(self, mock_init):
        """Test SMS sending failure."""
        # Mock Africa's Talking SMS service
        mock_sms = MagicMock()
        mock_response = {
            'SMSMessageData': {
                'Recipients': [{'statusCode': 400}]
            }
        }
        mock_sms.send.return_value = mock_response
        mock_init.return_value = mock_sms
        
        result = send_order_sms('+1234567890', 1)
        
        self.assertFalse(result)
    
    @patch('catalog.notifications.initialize_africastalking')
    def test_send_order_sms_no_service(self, mock_init):
        """Test SMS sending when service is not available."""
        mock_init.return_value = None
        
        result = send_order_sms('+1234567890', 1)
        
        self.assertFalse(result)
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_order_email_success(self):
        """Test successful email sending."""
        # Create an order
        order = Order.objects.create(customer=self.user)
        OrderItem.objects.create(
            order=order,
            product=self.iphone,
            quantity=1,
            purchase_price=self.iphone.price
        )
        
        result = send_order_email('admin@techmart.com', order.id)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'New Order #{order.id} - TechMart')
        self.assertIn('admin@techmart.com', mail.outbox[0].to)
    
    def test_send_order_email_order_not_found(self):
        """Test email sending when order doesn't exist."""
        result = send_order_email('admin@techmart.com', 999)
        
        self.assertFalse(result)
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_order_confirmation_email_success(self):
        """Test successful order confirmation email sending."""
        # Create an order
        order = Order.objects.create(customer=self.user)
        OrderItem.objects.create(
            order=order,
            product=self.iphone,
            quantity=1,
            purchase_price=self.iphone.price
        )
        
        result = send_order_confirmation_email('test@example.com', order.id)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Order Confirmation #{order.id} - TechMart')
        self.assertIn('test@example.com', mail.outbox[0].to)
    
    @patch('catalog.notifications.initialize_africastalking')
    def test_send_order_status_update_sms_success(self, mock_init):
        """Test successful status update SMS sending."""
        # Mock Africa's Talking SMS service
        mock_sms = MagicMock()
        mock_response = {
            'SMSMessageData': {
                'Recipients': [{'statusCode': 101}]
            }
        }
        mock_sms.send.return_value = mock_response
        mock_init.return_value = mock_sms
        
        result = send_order_status_update_sms('+1234567890', 1, 'confirmed')
        
        self.assertTrue(result)
        mock_sms.send.assert_called_once()
        
        # Check that the message contains order ID and status
        call_args = mock_sms.send.call_args
        message = call_args[0][0]
        self.assertIn('1', message)  # Order ID
        self.assertIn('confirmed', message.lower())


class CeleryTaskTestCase(BaseNotificationTestCase):
    """Test cases for Celery tasks."""
    
    @patch('catalog.notifications.send_order_sms')
    def test_send_order_sms_task_success(self, mock_send_sms):
        """Test successful SMS task execution."""
        mock_send_sms.return_value = True
        
        result = send_order_sms_task('+1234567890', 1)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['order_id'], 1)
        self.assertEqual(result['phone'], '+1234567890')
        mock_send_sms.assert_called_once_with('+1234567890', 1)
    
    @patch('catalog.notifications.send_order_sms')
    def test_send_order_sms_task_failure(self, mock_send_sms):
        """Test SMS task failure."""
        mock_send_sms.return_value = False
        
        result = send_order_sms_task('+1234567890', 1)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('catalog.notifications.send_order_email')
    def test_send_order_email_task_success(self, mock_send_email):
        """Test successful email task execution."""
        mock_send_email.return_value = True
        
        result = send_order_email_task('admin@techmart.com', 1)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['order_id'], 1)
        self.assertEqual(result['email'], 'admin@techmart.com')
        mock_send_email.assert_called_once_with('admin@techmart.com', 1)
    
    @patch('catalog.notifications.send_order_confirmation_email')
    def test_send_order_confirmation_email_task_success(self, mock_send_email):
        """Test successful confirmation email task execution."""
        mock_send_email.return_value = True
        
        result = send_order_confirmation_email_task('test@example.com', 1)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['order_id'], 1)
        self.assertEqual(result['email'], 'test@example.com')
        mock_send_email.assert_called_once_with('test@example.com', 1)
    
    @patch('catalog.notifications.send_order_status_update_sms')
    def test_send_order_status_update_sms_task_success(self, mock_send_sms):
        """Test successful status update SMS task execution."""
        mock_send_sms.return_value = True
        
        result = send_order_status_update_sms_task('+1234567890', 1, 'confirmed')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['order_id'], 1)
        self.assertEqual(result['phone'], '+1234567890')
        self.assertEqual(result['status'], 'confirmed')
        mock_send_sms.assert_called_once_with('+1234567890', 1, 'confirmed')
    
    @patch('catalog.tasks.send_order_sms_task.delay')
    @patch('catalog.tasks.send_order_email_task.delay')
    @patch('catalog.tasks.send_order_confirmation_email_task.delay')
    def test_process_order_notifications_success(self, mock_customer_email, mock_admin_email, mock_sms):
        """Test successful order notification processing."""
        # Create an order
        order = Order.objects.create(customer=self.user)
        OrderItem.objects.create(
            order=order,
            product=self.iphone,
            quantity=1,
            purchase_price=self.iphone.price
        )
        
        # Mock task delays
        mock_sms_task = MagicMock()
        mock_sms_task.id = 'sms-task-id'
        mock_sms.return_value = mock_sms_task
        
        mock_admin_email_task = MagicMock()
        mock_admin_email_task.id = 'admin-email-task-id'
        mock_admin_email.return_value = mock_admin_email_task
        
        mock_customer_email_task = MagicMock()
        mock_customer_email_task.id = 'customer-email-task-id'
        mock_customer_email.return_value = mock_customer_email_task
        
        result = process_order_notifications(order.id)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['order_id'], order.id)
        self.assertIn('tasks', result)
        self.assertEqual(result['tasks']['sms']['task_id'], 'sms-task-id')
        self.assertEqual(result['tasks']['admin_email']['task_id'], 'admin-email-task-id')
        self.assertEqual(result['tasks']['customer_email']['task_id'], 'customer-email-task-id')
    
    def test_process_order_notifications_order_not_found(self):
        """Test order notification processing when order doesn't exist."""
        result = process_order_notifications(999)
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['message'])


class OrderNotificationIntegrationTestCase(BaseNotificationTestCase):
    """Integration test cases for order notifications."""
    
    @patch('catalog.tasks.process_order_notifications.delay')
    def test_order_creation_triggers_notifications(self, mock_process_notifications):
        """Test that order creation triggers notification tasks."""
        # Mock OIDC authentication
        with patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True):
            # Get JWT token
            refresh = RefreshToken.for_user(self.user)
            access_token = str(refresh.access_token)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            # Create order
            url = reverse('catalog:order-list')
            data = {
                'items': [
                    {'product': self.iphone.id, 'quantity': 1}
                ]
            }
            
            response = self.client.post(url, data)
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify notification task was triggered
            mock_process_notifications.assert_called_once()
            order_id = response.data['id']
            mock_process_notifications.assert_called_with(order_id)
    
    @patch('catalog.tasks.send_order_status_update_sms_task.delay')
    def test_order_status_update_triggers_notifications(self, mock_status_sms):
        """Test that order status update triggers notification tasks."""
        # Create an order
        order = Order.objects.create(customer=self.user)
        OrderItem.objects.create(
            order=order,
            product=self.iphone,
            quantity=1,
            purchase_price=self.iphone.price
        )
        
        # Mock OIDC authentication for staff user
        with patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True):
            # Get JWT token for staff user
            refresh = RefreshToken.for_user(self.staff_user)
            access_token = str(refresh.access_token)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            # Update order status
            url = reverse('catalog:order-update-status', kwargs={'id': order.id})
            data = {'status': 'confirmed'}
            
            response = self.client.post(url, data)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify status update SMS task was triggered
            mock_status_sms.assert_called_once_with('+1234567890', order.id, 'confirmed')
    
    @patch('catalog.tasks.process_order_notifications.delay')
    def test_order_creation_without_phone_skips_sms(self, mock_process_notifications):
        """Test that order creation without customer phone skips SMS notifications."""
        # Create user without phone
        user_no_phone = User.objects.create_user(
            username='nophone',
            email='nophone@example.com',
            password='testpass123'
        )
        CustomerProfile.objects.create(
            user=user_no_phone,
            phone='',  # No phone number
            address='123 Test Street'
        )
        
        # Mock OIDC authentication
        with patch('catalog.permissions.IsOIDCAuthenticated.has_permission', return_value=True):
            # Get JWT token
            refresh = RefreshToken.for_user(user_no_phone)
            access_token = str(refresh.access_token)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            # Create order
            url = reverse('catalog:order-list')
            data = {
                'items': [
                    {'product': self.iphone.id, 'quantity': 1}
                ]
            }
            
            response = self.client.post(url, data)
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify notification task was still triggered (but SMS will be skipped)
            mock_process_notifications.assert_called_once()


class MockAfricaTalkingTestCase(BaseNotificationTestCase):
    """Test cases with mocked Africa's Talking API."""
    
    @patch('catalog.notifications.africastalking')
    def test_africastalking_sms_mock(self, mock_africastalking):
        """Test SMS functionality with mocked Africa's Talking API."""
        # Mock the SMS service
        mock_sms = MagicMock()
        mock_response = {
            'SMSMessageData': {
                'Recipients': [{'statusCode': 101}]
            }
        }
        mock_sms.send.return_value = mock_response
        mock_africastalking.SMS = MagicMock(return_value=mock_sms)
        
        # Test SMS sending
        result = send_order_sms('+1234567890', 1)
        
        self.assertTrue(result)
        mock_africastalking.initialize.assert_called_once()
        mock_sms.send.assert_called_once()
        
        # Verify the message content
        call_args = mock_sms.send.call_args
        message = call_args[0][0]
        phone_numbers = call_args[0][1]
        
        self.assertIn('order', message.lower())
        self.assertIn('1', message)  # Order ID
        self.assertEqual(phone_numbers, ['+1234567890'])
    
    @patch('catalog.notifications.africastalking')
    def test_africastalking_sms_error_handling(self, mock_africastalking):
        """Test SMS error handling with mocked Africa's Talking API."""
        # Mock the SMS service to raise an exception
        mock_africastalking.initialize.side_effect = Exception("API Error")
        
        # Test SMS sending
        result = send_order_sms('+1234567890', 1)
        
        self.assertFalse(result)


class EmailContentTestCase(BaseNotificationTestCase):
    """Test cases for email content."""
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_content_rendering(self):
        """Test that email content renders correctly."""
        # Create an order
        order = Order.objects.create(customer=self.user)
        OrderItem.objects.create(
            order=order,
            product=self.iphone,
            quantity=2,
            purchase_price=self.iphone.price
        )
        
        # Send email
        result = send_order_email('admin@techmart.com', order.id)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('New Order', email.subject)
        self.assertIn(str(order.id), email.subject)
        self.assertIn('admin@techmart.com', email.to)
        
        # Check plain text content
        self.assertIn('TechMart', email.body)
        self.assertIn(str(order.id), email.body)
        self.assertIn('iPhone 15', email.body)
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_confirmation_email_content_rendering(self):
        """Test that confirmation email content renders correctly."""
        # Create an order
        order = Order.objects.create(customer=self.user)
        OrderItem.objects.create(
            order=order,
            product=self.iphone,
            quantity=1,
            purchase_price=self.iphone.price
        )
        
        # Send confirmation email
        result = send_order_confirmation_email('test@example.com', order.id)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('Order Confirmation', email.subject)
        self.assertIn(str(order.id), email.subject)
        self.assertIn('test@example.com', email.to)
        
        # Check plain text content
        self.assertIn('Thank you', email.body)
        self.assertIn(str(order.id), email.body)
        self.assertIn('iPhone 15', email.body)
