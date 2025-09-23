from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.db.models import Q
from django.contrib.auth.models import User

from .models import CustomerProfile, Category, Product, Order, OrderItem
from .serializers import (
    CustomerProfileSerializer, CategorySerializer, CategoryListSerializer,
    ProductSerializer, OrderSerializer, OrderCreateSerializer,
    CategoryAveragePriceSerializer
)
from .permissions import IsAuthenticatedOrReadOnlyForStaff, IsOwnerOrStaff, IsOIDCAuthenticated


class CustomerProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for CustomerProfile model."""
    
    queryset = CustomerProfile.objects.select_related('user').all()
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsOIDCAuthenticated, IsOwnerOrStaff]
    
    def get_queryset(self):
        """Filter profiles based on user permissions."""
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Register a new customer account.
        
        POST /customer-profiles/register/
        Body: {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "address": "123 Main St, City, State 12345"
        }
        """
        from django.contrib.auth import authenticate
        from rest_framework_simplejwt.tokens import RefreshToken
        
        # Extract user data
        user_data = {
            'username': request.data.get('username'),
            'email': request.data.get('email'),
            'password': request.data.get('password'),
            'first_name': request.data.get('first_name', ''),
            'last_name': request.data.get('last_name', ''),
        }
        
        # Extract profile data
        profile_data = {
            'phone': request.data.get('phone', ''),
            'address': request.data.get('address', ''),
        }
        
        # Validate required fields
        if not all([user_data['username'], user_data['email'], user_data['password']]):
            return Response(
                {'error': 'Username, email, and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already exists
        if User.objects.filter(username=user_data['username']).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=user_data['email']).exists():
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create user
            user = User.objects.create_user(**user_data)
            
            # Create customer profile
            profile = CustomerProfile.objects.create(
                user=user,
                phone=profile_data['phone'],
                address=profile_data['address']
            )
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Return user data and tokens
            return Response({
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'profile': {
                    'id': profile.id,
                    'phone': profile.phone,
                    'address': profile.address,
                },
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Registration failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Category model with MPTT hierarchy support."""
    
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnlyForStaff]  # Public read access, authenticated write access
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views."""
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer
    
    def get_queryset(self):
        """Filter categories based on query parameters."""
        queryset = Category.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by parent
        parent_id = self.request.query_params.get('parent')
        if parent_id is not None:
            if parent_id == 'null':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_id)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('name')
    
    @action(detail=True, methods=['get'])
    def average_price(self, request, id=None):
        """
        Get average price for a category and its descendants.
        
        GET /categories/{id}/average_price/
        """
        category = self.get_object()
        
        # Get all descendant categories
        descendants = category.get_descendants(include_self=True)
        descendant_names = [desc.name for desc in descendants]
        
        # Calculate average price
        avg_price = category.get_average_price()
        
        # Count products in this category and descendants
        product_count = Product.objects.filter(
            category__in=descendants,
            is_active=True
        ).count()
        
        serializer = CategoryAveragePriceSerializer({
            'category_id': category.id,
            'category_name': category.name,
            'average_price': avg_price,
            'product_count': product_count,
            'descendant_categories': descendant_names
        })
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Get category tree structure.
        
        GET /categories/tree/
        """
        root_categories = Category.objects.filter(parent__isnull=True, is_active=True)
        serializer = CategorySerializer(root_categories, many=True, context={'request': request})
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model."""
    
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnlyForStaff]  # Public read access, authenticated write access
    
    def get_queryset(self):
        """Filter products based on query parameters."""
        queryset = Product.objects.select_related('category').all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by stock status
        in_stock = self.request.query_params.get('in_stock')
        if in_stock is not None:
            if in_stock.lower() == 'true':
                queryset = queryset.filter(stock_quantity__gt=0)
            else:
                queryset = queryset.filter(stock_quantity=0)
        
        # Price range filter
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Search by name or SKU
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )
        
        return queryset.order_by('name')
    
    @action(detail=True, methods=['post'])
    def add_stock(self, request, id=None):
        """
        Add stock to a product.
        
        POST /products/{id}/add_stock/
        Body: {"quantity": 10}
        """
        product = self.get_object()
        quantity = request.data.get('quantity')
        
        if not quantity or not isinstance(quantity, int) or quantity <= 0:
            return Response(
                {'error': 'Valid quantity is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product.add_stock(quantity)
        
        serializer = self.get_serializer(product)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reduce_stock(self, request, id=None):
        """
        Reduce stock from a product.
        
        POST /products/{id}/reduce_stock/
        Body: {"quantity": 5}
        """
        product = self.get_object()
        quantity = request.data.get('quantity')
        
        if not quantity or not isinstance(quantity, int) or quantity <= 0:
            return Response(
                {'error': 'Valid quantity is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not product.reduce_stock(quantity):
            return Response(
                {'error': 'Insufficient stock'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(product)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order model."""
    
    queryset = Order.objects.select_related('customer').prefetch_related('items__product').all()
    permission_classes = [IsOIDCAuthenticated, IsOwnerOrStaff]
    
    def get_serializer_class(self):
        """Use different serializers for create and other actions."""
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        """Filter orders based on user permissions."""
        queryset = Order.objects.select_related('customer').prefetch_related('items__product').all()
        
        # Non-staff users can only see their own orders
        if not self.request.user.is_staff:
            queryset = queryset.filter(customer=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set customer to current user if not staff and trigger notifications."""
        if not self.request.user.is_staff:
            order = serializer.save(customer=self.request.user)
        else:
            order = serializer.save()
        
        # Trigger notification tasks after order is created
        self._trigger_order_notifications(order)
    
    def _trigger_order_notifications(self, order):
        """Trigger notification tasks for a new order."""
        try:
            from .tasks import process_order_notifications
            
            # Start the notification processing task
            task = process_order_notifications.delay(order.id)
            
            # Log the task start
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Order notification task started for order {order.id}: {task.id}")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to trigger notifications for order {order.id}: {e}")
            # Don't raise the exception to avoid breaking the order creation
    
    def _trigger_status_update_notification(self, order, new_status):
        """Trigger status update notification for an order."""
        try:
            from .tasks import send_order_status_update_sms_task
            
            # Get customer phone from profile
            customer_phone = None
            if hasattr(order.customer, 'profile') and order.customer.profile.phone:
                customer_phone = order.customer.profile.phone
            
            if customer_phone:
                # Start the status update SMS task
                task = send_order_status_update_sms_task.delay(customer_phone, order.id, new_status)
                
                # Log the task start
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Status update SMS task started for order {order.id}: {task.id}")
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"No phone number available for customer {order.customer.id}, skipping status update SMS")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to trigger status update notification for order {order.id}: {e}")
            # Don't raise the exception to avoid breaking the status update
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, id=None):
        """
        Cancel an order.
        
        POST /orders/{id}/cancel/
        """
        order = self.get_object()
        
        if not order.can_be_cancelled():
            return Response(
                {'error': 'Order cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Restore stock for all items
        for item in order.items.all():
            item.product.add_stock(item.quantity)
        
        order.status = 'cancelled'
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, id=None):
        """
        Update order status (staff only).
        
        POST /orders/{id}/update_status/
        Body: {"status": "confirmed"}
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status or new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Valid status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save()
        
        # Send status update notification to customer
        self._trigger_status_update_notification(order, new_status)
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
