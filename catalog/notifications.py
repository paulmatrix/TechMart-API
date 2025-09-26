import africastalking
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


def initialize_africastalking():
    """Initialize Africa's Talking SDK."""
    try:
        # Initialize Africa's Talking
        africastalking.initialize(
            username=settings.AFRICASTALKING_USERNAME,
            api_key=settings.AFRICASTALKING_API_KEY
        )
        # Return the SMS service class, not an instance
        return africastalking.SMS
    except Exception as e:
        logger.error(f"Failed to initialize Africa's Talking: {e}")
        return None


def send_order_sms(customer_phone, order_id):
    """
    Send SMS notification to customer about their order.
    
    Args:
        customer_phone (str): Customer's phone number
        order_id (int): Order ID
    
    Returns:
        bool: True if SMS was sent successfully, False otherwise
    """
    try:
        # Initialize Africa's Talking SMS service
        sms = initialize_africastalking()
        if not sms:
            logger.error("Failed to initialize Africa's Talking SMS service")
            return False
        
        # Format phone number (ensure it starts with +)
        if not customer_phone.startswith('+'):
            customer_phone = '+' + customer_phone.lstrip('+')
        
        # Create SMS message
        message = f"Thank you for your order! Your order #{order_id} has been received and is being processed. We'll notify you when it's ready for delivery."
        
        # Send SMS
        response = sms.send(message, [customer_phone])
        
        if response and response.get('SMSMessageData', {}).get('Recipients'):
            recipients = response['SMSMessageData']['Recipients']
            if recipients and recipients[0].get('statusCode') == 101:
                logger.info(f"SMS sent successfully to {customer_phone} for order {order_id}")
                return True
            else:
                logger.error(f"SMS failed to send to {customer_phone}: {recipients}")
                return False
        else:
            logger.error(f"Invalid response from Africa's Talking: {response}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending SMS to {customer_phone} for order {order_id}: {e}")
        return False


def send_order_email(admin_email, order_id):
    """
    Send email notification to admin about new order.
    
    Args:
        admin_email (str): Admin's email address
        order_id (int): Order ID
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        from .models import Order
        
        # Get order details
        try:
            order = Order.objects.select_related('customer').prefetch_related('items__product').get(id=order_id)
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found")
            return False
        
        # Prepare email content
        subject = f'New Order #{order_id} - TechMart'
        
        # Create plain text email content
        order_items = order.items.all()
        items_text = "\n".join([
            f"- {item.product.name} ({item.product.sku}) x{item.quantity} @ ${item.purchase_price}"
            for item in order_items
        ])
        
        plain_message = f"""
New Order Notification - TechMart

Order Information:
- Order ID: #{order.id}
- Customer: {order.customer.get_full_name() or order.customer.username}
- Email: {order.customer.email}
- Order Date: {order.created_at.strftime('%B %d, %Y %H:%M')}
- Status: {order.get_status_display()}

Order Items:
{items_text}

Total Amount: ${order.total}

Please process this order and update the customer accordingly.

This is an automated notification from TechMart API
Order ID: {order.id} | {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        
        logger.info(f"Email sent successfully to {admin_email} for order {order_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {admin_email} for order {order_id}: {e}")
        return False


def send_order_confirmation_email(customer_email, order_id):
    """
    Send order confirmation email to customer.
    
    Args:
        customer_email (str): Customer's email address
        order_id (int): Order ID
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        from .models import Order
        
        # Get order details
        try:
            order = Order.objects.select_related('customer').prefetch_related('items__product').get(id=order_id)
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found")
            return False
        
        # Prepare email content
        subject = f'Order Confirmation #{order_id} - TechMart'
        
        # Create plain text email content
        order_items = order.items.all()
        items_text = "\n".join([
            f"- {item.product.name} ({item.product.sku}) x{item.quantity} @ ${item.purchase_price}"
            for item in order_items
        ])
        
        plain_message = f"""
Order Confirmation - TechMart

Thank you for your order, {order.customer.get_full_name() or order.customer.username}!

Your order has been successfully received and is being processed.

Order Information:
- Order ID: #{order.id}
- Order Date: {order.created_at.strftime('%B %d, %Y %H:%M')}
- Status: {order.get_status_display()}

Order Items:
{items_text}

Total Amount: ${order.total}

What's Next?
- We'll process your order and prepare it for shipping
- You'll receive SMS updates about your order status
- Once shipped, you'll get tracking information
- Expected delivery time: 3-5 business days

If you have any questions about your order, please contact our customer service team.

Thank you for choosing TechMart!

Order ID: {order.id} | {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer_email],
            fail_silently=False,
        )
        
        logger.info(f"Order confirmation email sent successfully to {customer_email} for order {order_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending order confirmation email to {customer_email} for order {order_id}: {e}")
        return False


def send_order_status_update_sms(customer_phone, order_id, status):
    """
    Send SMS notification to customer about order status update.
    
    Args:
        customer_phone (str): Customer's phone number
        order_id (int): Order ID
        status (str): New order status
    
    Returns:
        bool: True if SMS was sent successfully, False otherwise
    """
    try:
        # Initialize Africa's Talking SMS service
        sms = initialize_africastalking()
        if not sms:
            logger.error("Failed to initialize Africa's Talking SMS service")
            return False
        
        # Format phone number
        if not customer_phone.startswith('+'):
            customer_phone = '+' + customer_phone.lstrip('+')
        
        # Create status-specific message
        status_messages = {
            'confirmed': f"Great news! Your order #{order_id} has been confirmed and is being prepared.",
            'processing': f"Your order #{order_id} is now being processed and will be ready soon.",
            'shipped': f"Your order #{order_id} has been shipped! Track your package for delivery updates.",
            'delivered': f"Your order #{order_id} has been delivered! Thank you for shopping with TechMart.",
            'cancelled': f"We're sorry, but your order #{order_id} has been cancelled. Please contact us if you have any questions.",
        }
        
        message = status_messages.get(status, f"Your order #{order_id} status has been updated to {status}.")
        
        # Send SMS
        response = sms.send(message, [customer_phone])
        
        if response and response.get('SMSMessageData', {}).get('Recipients'):
            recipients = response['SMSMessageData']['Recipients']
            if recipients and recipients[0].get('statusCode') == 101:
                logger.info(f"Status update SMS sent successfully to {customer_phone} for order {order_id}")
                return True
            else:
                logger.error(f"Status update SMS failed to send to {customer_phone}: {recipients}")
                return False
        else:
            logger.error(f"Invalid response from Africa's Talking: {response}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending status update SMS to {customer_phone} for order {order_id}: {e}")
        return False
