from celery import shared_task
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_order_sms_task(self, customer_phone, order_id):
    """
    Celery task to send SMS notification to customer about their order.
    
    Args:
        customer_phone (str): Customer's phone number
        order_id (int): Order ID
    
    Returns:
        dict: Task result with success status and message
    """
    try:
        from .notifications import send_order_sms
        
        logger.info(f"Starting SMS task for order {order_id} to {customer_phone}")
        
        success = send_order_sms(customer_phone, order_id)
        
        if success:
            logger.info(f"SMS task completed successfully for order {order_id}")
            return {
                'success': True,
                'message': f'SMS sent successfully to {customer_phone} for order {order_id}',
                'order_id': order_id,
                'phone': customer_phone
            }
        else:
            logger.error(f"SMS task failed for order {order_id}")
            raise Exception(f"Failed to send SMS to {customer_phone} for order {order_id}")
            
    except Exception as exc:
        logger.error(f"SMS task error for order {order_id}: {exc}")
        
        # Retry the task with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
            logger.info(f"Retrying SMS task for order {order_id} in {retry_delay} seconds")
            raise self.retry(countdown=retry_delay, exc=exc)
        else:
            logger.error(f"SMS task failed permanently for order {order_id} after {self.max_retries} retries")
            return {
                'success': False,
                'message': f'SMS failed permanently for order {order_id} after {self.max_retries} retries',
                'order_id': order_id,
                'phone': customer_phone,
                'error': str(exc)
            }


@shared_task(bind=True, max_retries=3)
def send_order_email_task(self, admin_email, order_id):
    """
    Celery task to send email notification to admin about new order.
    
    Args:
        admin_email (str): Admin's email address
        order_id (int): Order ID
    
    Returns:
        dict: Task result with success status and message
    """
    try:
        from .notifications import send_order_email
        
        logger.info(f"Starting email task for order {order_id} to {admin_email}")
        
        success = send_order_email(admin_email, order_id)
        
        if success:
            logger.info(f"Email task completed successfully for order {order_id}")
            return {
                'success': True,
                'message': f'Email sent successfully to {admin_email} for order {order_id}',
                'order_id': order_id,
                'email': admin_email
            }
        else:
            logger.error(f"Email task failed for order {order_id}")
            raise Exception(f"Failed to send email to {admin_email} for order {order_id}")
            
    except Exception as exc:
        logger.error(f"Email task error for order {order_id}: {exc}")
        
        # Retry the task with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
            logger.info(f"Retrying email task for order {order_id} in {retry_delay} seconds")
            raise self.retry(countdown=retry_delay, exc=exc)
        else:
            logger.error(f"Email task failed permanently for order {order_id} after {self.max_retries} retries")
            return {
                'success': False,
                'message': f'Email failed permanently for order {order_id} after {self.max_retries} retries',
                'order_id': order_id,
                'email': admin_email,
                'error': str(exc)
            }


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email_task(self, customer_email, order_id):
    """
    Celery task to send order confirmation email to customer.
    
    Args:
        customer_email (str): Customer's email address
        order_id (int): Order ID
    
    Returns:
        dict: Task result with success status and message
    """
    try:
        from .notifications import send_order_confirmation_email
        
        logger.info(f"Starting confirmation email task for order {order_id} to {customer_email}")
        
        success = send_order_confirmation_email(customer_email, order_id)
        
        if success:
            logger.info(f"Confirmation email task completed successfully for order {order_id}")
            return {
                'success': True,
                'message': f'Confirmation email sent successfully to {customer_email} for order {order_id}',
                'order_id': order_id,
                'email': customer_email
            }
        else:
            logger.error(f"Confirmation email task failed for order {order_id}")
            raise Exception(f"Failed to send confirmation email to {customer_email} for order {order_id}")
            
    except Exception as exc:
        logger.error(f"Confirmation email task error for order {order_id}: {exc}")
        
        # Retry the task with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
            logger.info(f"Retrying confirmation email task for order {order_id} in {retry_delay} seconds")
            raise self.retry(countdown=retry_delay, exc=exc)
        else:
            logger.error(f"Confirmation email task failed permanently for order {order_id} after {self.max_retries} retries")
            return {
                'success': False,
                'message': f'Confirmation email failed permanently for order {order_id} after {self.max_retries} retries',
                'order_id': order_id,
                'email': customer_email,
                'error': str(exc)
            }


@shared_task(bind=True, max_retries=3)
def send_order_status_update_sms_task(self, customer_phone, order_id, status):
    """
    Celery task to send SMS notification to customer about order status update.
    
    Args:
        customer_phone (str): Customer's phone number
        order_id (int): Order ID
        status (str): New order status
    
    Returns:
        dict: Task result with success status and message
    """
    try:
        from .notifications import send_order_status_update_sms
        
        logger.info(f"Starting status update SMS task for order {order_id} to {customer_phone}")
        
        success = send_order_status_update_sms(customer_phone, order_id, status)
        
        if success:
            logger.info(f"Status update SMS task completed successfully for order {order_id}")
            return {
                'success': True,
                'message': f'Status update SMS sent successfully to {customer_phone} for order {order_id}',
                'order_id': order_id,
                'phone': customer_phone,
                'status': status
            }
        else:
            logger.error(f"Status update SMS task failed for order {order_id}")
            raise Exception(f"Failed to send status update SMS to {customer_phone} for order {order_id}")
            
    except Exception as exc:
        logger.error(f"Status update SMS task error for order {order_id}: {exc}")
        
        # Retry the task with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
            logger.info(f"Retrying status update SMS task for order {order_id} in {retry_delay} seconds")
            raise self.retry(countdown=retry_delay, exc=exc)
        else:
            logger.error(f"Status update SMS task failed permanently for order {order_id} after {self.max_retries} retries")
            return {
                'success': False,
                'message': f'Status update SMS failed permanently for order {order_id} after {self.max_retries} retries',
                'order_id': order_id,
                'phone': customer_phone,
                'status': status,
                'error': str(exc)
            }


@shared_task
def process_order_notifications(order_id):
    """
    Process all notifications for a new order.
    This task coordinates sending SMS to customer and email to admin.
    
    Args:
        order_id (int): Order ID
    
    Returns:
        dict: Combined results of all notification tasks
    """
    try:
        from .models import Order
        
        logger.info(f"Processing notifications for order {order_id}")
        
        # Get order details
        try:
            order = Order.objects.select_related('customer', 'customer__profile').get(id=order_id)
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found")
            return {
                'success': False,
                'message': f'Order {order_id} not found',
                'order_id': order_id
            }
        
        # Get customer phone from profile
        customer_phone = None
        if hasattr(order.customer, 'profile') and order.customer.profile.phone:
            customer_phone = order.customer.profile.phone
        
        # Get admin email from settings
        admin_email = settings.ADMIN_EMAIL
        
        # Start notification tasks
        results = {
            'order_id': order_id,
            'customer_email': order.customer.email,
            'customer_phone': customer_phone,
            'admin_email': admin_email,
            'tasks': {}
        }
        
        # Send SMS to customer if phone is available
        if customer_phone:
            sms_task = send_order_sms_task.delay(customer_phone, order_id)
            results['tasks']['sms'] = {
                'task_id': sms_task.id,
                'status': 'started'
            }
            logger.info(f"SMS task started for order {order_id}: {sms_task.id}")
        else:
            logger.warning(f"No phone number available for customer {order.customer.id}, skipping SMS")
            results['tasks']['sms'] = {
                'status': 'skipped',
                'reason': 'No phone number available'
            }
        
        # Send email to admin
        admin_email_task = send_order_email_task.delay(admin_email, order_id)
        results['tasks']['admin_email'] = {
            'task_id': admin_email_task.id,
            'status': 'started'
        }
        logger.info(f"Admin email task started for order {order_id}: {admin_email_task.id}")
        
        # Send confirmation email to customer
        if order.customer.email:
            customer_email_task = send_order_confirmation_email_task.delay(order.customer.email, order_id)
            results['tasks']['customer_email'] = {
                'task_id': customer_email_task.id,
                'status': 'started'
            }
            logger.info(f"Customer email task started for order {order_id}: {customer_email_task.id}")
        else:
            logger.warning(f"No email available for customer {order.customer.id}, skipping confirmation email")
            results['tasks']['customer_email'] = {
                'status': 'skipped',
                'reason': 'No email available'
            }
        
        results['success'] = True
        results['message'] = f'All notification tasks started for order {order_id}'
        
        logger.info(f"All notification tasks started for order {order_id}")
        return results
        
    except Exception as e:
        logger.error(f"Error processing notifications for order {order_id}: {e}")
        return {
            'success': False,
            'message': f'Error processing notifications for order {order_id}: {str(e)}',
            'order_id': order_id,
            'error': str(e)
        }
