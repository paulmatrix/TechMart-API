# TechMart API Notifications Guide

## Overview

The TechMart API implements a comprehensive notification system using **Africa's Talking SMS** and **Django Email** with **Celery** for asynchronous processing. This ensures customers and administrators are promptly notified about order events.

## Architecture

### Components
- **Africa's Talking**: SMS notifications to customers
- **Django Email**: Email notifications to customers and admins
- **Celery**: Asynchronous task processing
- **Redis**: Message broker for Celery
- **HTML Templates**: Rich email content

### Notification Flow
```
Order Created → Celery Task → SMS to Customer + Email to Admin + Confirmation Email to Customer
Order Status Updated → Celery Task → SMS to Customer
```

## Configuration

### Environment Variables

```env
# Africa's Talking SMS Configuration
AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=your-africastalking-api-key-here

# Email Configuration
ADMIN_EMAIL=admin@techmart.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Django Settings

```python
# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER', default='noreply@techmart.com')
ADMIN_EMAIL = config('ADMIN_EMAIL', default='admin@techmart.com')

# Africa's Talking Configuration
AFRICASTALKING_USERNAME = config('AFRICASTALKING_USERNAME', default='sandbox')
AFRICASTALKING_API_KEY = config('AFRICASTALKING_API_KEY', default='')
```

## Notification Types

### 1. Order Creation Notifications

When a new order is created, the system automatically sends:

#### SMS to Customer
- **Trigger**: Order creation
- **Content**: Order confirmation with order ID
- **Example**: "Thank you for your order! Your order #123 has been received and is being processed."

#### Email to Admin
- **Trigger**: Order creation
- **Content**: Detailed order information with items and totals
- **Template**: `emails/new_order_notification.html`

#### Confirmation Email to Customer
- **Trigger**: Order creation
- **Content**: Order confirmation with details and next steps
- **Template**: `emails/order_confirmation.html`

### 2. Order Status Update Notifications

When an order status is updated, the system sends:

#### SMS to Customer
- **Trigger**: Status change (confirmed, processing, shipped, delivered, cancelled)
- **Content**: Status-specific message with order ID
- **Examples**:
  - Confirmed: "Great news! Your order #123 has been confirmed and is being prepared."
  - Shipped: "Your order #123 has been shipped! Track your package for delivery updates."

## API Integration

### Order Creation with Notifications

```python
# When creating an order via API
POST /api/v1/orders/
{
    "items": [
        {"product": 1, "quantity": 2},
        {"product": 2, "quantity": 1}
    ]
}

# Automatically triggers:
# 1. SMS to customer (if phone available)
# 2. Email to admin
# 3. Confirmation email to customer
```

### Order Status Update with Notifications

```python
# When updating order status via API
POST /api/v1/orders/{id}/update_status/
{
    "status": "confirmed"
}

# Automatically triggers:
# 1. SMS to customer (if phone available)
```

## Celery Tasks

### Task Structure

```python
# Main coordination task
@shared_task
def process_order_notifications(order_id):
    """Process all notifications for a new order."""
    # Coordinates SMS, admin email, and customer email

# Individual notification tasks
@shared_task(bind=True, max_retries=3)
def send_order_sms_task(self, customer_phone, order_id):
    """Send SMS notification to customer."""

@shared_task(bind=True, max_retries=3)
def send_order_email_task(self, admin_email, order_id):
    """Send email notification to admin."""

@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email_task(self, customer_email, order_id):
    """Send confirmation email to customer."""

@shared_task(bind=True, max_retries=3)
def send_order_status_update_sms_task(self, customer_phone, order_id, status):
    """Send status update SMS to customer."""
```

### Task Features
- **Retry Logic**: 3 retries with exponential backoff
- **Error Handling**: Comprehensive error logging
- **Async Processing**: Non-blocking order creation
- **Task Tracking**: Unique task IDs for monitoring

## Email Templates

### New Order Notification (Admin)
- **File**: `catalog/templates/emails/new_order_notification.html`
- **Content**: Order details, customer info, itemized list, totals
- **Styling**: Professional HTML with TechMart branding

### Order Confirmation (Customer)
- **File**: `catalog/templates/emails/order_confirmation.html`
- **Content**: Thank you message, order details, next steps
- **Styling**: Customer-friendly design with clear information

## SMS Messages

### Order Creation SMS
```
Thank you for your order! Your order #{order_id} has been received and is being processed. We'll notify you when it's ready for delivery.
```

### Status Update SMS Messages
```python
status_messages = {
    'confirmed': "Great news! Your order #{order_id} has been confirmed and is being prepared.",
    'processing': "Your order #{order_id} is now being processed and will be ready soon.",
    'shipped': "Your order #{order_id} has been shipped! Track your package for delivery updates.",
    'delivered': "Your order #{order_id} has been delivered! Thank you for shopping with TechMart.",
    'cancelled': "We're sorry, but your order #{order_id} has been cancelled. Please contact us if you have any questions.",
}
```

## Docker Setup

### Services
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  celery:
    build: .
    command: celery -A config worker -l info
    depends_on:
      - redis
      - db
```

### Running Celery
```bash
# Start Celery worker
docker-compose exec celery celery -A config worker -l info

# Start Celery beat (for scheduled tasks)
docker-compose exec celery celery -A config beat -l info

# Monitor Celery tasks
docker-compose exec celery celery -A config flower
```

## Testing

### Running Notification Tests
```bash
# Run all notification tests
docker-compose exec web pytest catalog/tests/test_notifications.py -v

# Run specific test class
docker-compose exec web pytest catalog/tests/test_notifications.py::NotificationFunctionTestCase -v

# Run with coverage
docker-compose exec web pytest catalog/tests/test_notifications.py --cov=catalog.notifications --cov=catalog.tasks
```

### Test Categories
1. **NotificationFunctionTestCase**: Core notification functions
2. **CeleryTaskTestCase**: Celery task execution
3. **OrderNotificationIntegrationTestCase**: API integration
4. **MockAfricaTalkingTestCase**: Africa's Talking API mocking
5. **EmailTemplateTestCase**: Email template rendering

### Mocking for Testing
```python
# Mock Africa's Talking API
@patch('catalog.notifications.africastalking')
def test_sms_functionality(mock_africastalking):
    # Test implementation

# Mock Django email backend
@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
def test_email_functionality():
    # Test implementation
```

## Monitoring and Logging

### Logging Configuration
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'catalog.notifications': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'catalog.tasks': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

### Monitoring Tasks
```bash
# Check Celery worker status
docker-compose exec celery celery -A config inspect active

# Check task results
docker-compose exec celery celery -A config inspect scheduled

# Monitor task execution
docker-compose exec celery celery -A config events
```

## Error Handling

### SMS Failures
- **Retry Logic**: 3 attempts with exponential backoff
- **Fallback**: Log error, continue with other notifications
- **Monitoring**: Track failure rates and patterns

### Email Failures
- **Retry Logic**: 3 attempts with exponential backoff
- **Fallback**: Log error, continue with other notifications
- **SMTP Errors**: Handle authentication and connection issues

### Task Failures
- **Dead Letter Queue**: Failed tasks after max retries
- **Error Logging**: Comprehensive error tracking
- **Alerting**: Monitor critical failures

## Production Deployment

### Africa's Talking Setup
1. **Create Account**: Sign up at africastalking.com
2. **Get API Key**: Generate API key for your application
3. **Configure Endpoints**: Set up webhook endpoints if needed
4. **Test Sandbox**: Use sandbox environment for testing

### Email Configuration
1. **SMTP Provider**: Configure Gmail, SendGrid, or other provider
2. **Authentication**: Set up app passwords or API keys
3. **Rate Limits**: Configure appropriate sending limits
4. **Monitoring**: Set up email delivery monitoring

### Redis Configuration
1. **Persistence**: Configure Redis persistence for task durability
2. **Memory**: Allocate sufficient memory for task queue
3. **Monitoring**: Set up Redis monitoring and alerting
4. **Backup**: Configure regular backups

### Celery Configuration
1. **Workers**: Scale workers based on notification volume
2. **Monitoring**: Use Flower for task monitoring
3. **Scaling**: Configure horizontal scaling for high volume
4. **Health Checks**: Set up worker health monitoring

## Troubleshooting

### Common Issues

#### SMS Not Sending
```bash
# Check Africa's Talking configuration
docker-compose exec web python manage.py shell
>>> from catalog.notifications import initialize_africastalking
>>> sms = initialize_africastalking()
>>> print(sms)  # Should return SMS service object
```

#### Email Not Sending
```bash
# Test email configuration
docker-compose exec web python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

#### Celery Tasks Not Processing
```bash
# Check Celery worker status
docker-compose exec celery celery -A config inspect active

# Check Redis connection
docker-compose exec redis redis-cli ping
```

#### Task Failures
```bash
# Check failed tasks
docker-compose exec celery celery -A config inspect failed

# Check task logs
docker-compose logs celery
```

### Debug Mode
```python
# Enable debug logging
LOGGING = {
    'loggers': {
        'catalog.notifications': {
            'level': 'DEBUG',
        },
        'catalog.tasks': {
            'level': 'DEBUG',
        },
    },
}
```

## Security Considerations

### API Keys
- **Environment Variables**: Store API keys in environment variables
- **Secrets Management**: Use proper secrets management in production
- **Rotation**: Regularly rotate API keys
- **Access Control**: Limit API key permissions

### Email Security
- **TLS**: Always use TLS for SMTP connections
- **Authentication**: Use strong authentication methods
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Content Filtering**: Filter email content for security

### SMS Security
- **Phone Validation**: Validate phone numbers before sending
- **Rate Limiting**: Implement SMS rate limiting
- **Content Filtering**: Filter SMS content for security
- **Cost Monitoring**: Monitor SMS costs and usage

## Performance Optimization

### Celery Optimization
- **Worker Scaling**: Scale workers based on load
- **Task Batching**: Batch similar tasks when possible
- **Queue Routing**: Use separate queues for different task types
- **Memory Management**: Configure worker memory limits

### Redis Optimization
- **Memory Usage**: Monitor and optimize Redis memory usage
- **Persistence**: Configure appropriate persistence settings
- **Connection Pooling**: Use connection pooling for better performance
- **Monitoring**: Set up Redis performance monitoring

### Email Optimization
- **Template Caching**: Cache email templates for better performance
- **Async Sending**: Use async email sending for better throughput
- **Batch Processing**: Process emails in batches when possible
- **CDN**: Use CDN for email template assets

## Future Enhancements

### Planned Features
- **Push Notifications**: Mobile app push notifications
- **Webhook Support**: Webhook notifications for external systems
- **Notification Preferences**: User-configurable notification preferences
- **Multi-language Support**: Support for multiple languages
- **Rich Media**: Support for rich media in notifications
- **Analytics**: Notification delivery and engagement analytics

### Integration Opportunities
- **Slack Integration**: Admin notifications via Slack
- **WhatsApp Integration**: WhatsApp Business API integration
- **SMS Providers**: Support for multiple SMS providers
- **Email Providers**: Support for multiple email providers
- **CRM Integration**: Integration with customer relationship management systems
