from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CustomerProfile, Category, Product, Order, OrderItem


class CustomerProfileSerializer(serializers.ModelSerializer):
    """Serializer for CustomerProfile model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'user', 'user_email', 'user_first_name', 'user_last_name',
            'phone', 'address', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model with MPTT hierarchy support."""
    
    children = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_name',
            'is_active', 'children', 'product_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'slug': {'required': False, 'allow_blank': True}
        }
    
    def create(self, validated_data):
        """Create category with auto-generated or custom slug."""
        from django.utils.text import slugify
        
        name = validated_data['name']
        
        # Use provided slug or generate from name
        if 'slug' in validated_data and validated_data['slug'] and validated_data['slug'].strip():
            base_slug = slugify(validated_data['slug'])
        else:
            base_slug = slugify(name)
        
        slug = base_slug
        
        # Ensure slug is unique
        counter = 1
        while Category.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        validated_data['slug'] = slug
        return super().create(validated_data)
    
    def get_children(self, obj):
        """Get direct children of the category."""
        children = obj.get_children()
        return CategorySerializer(children, many=True, context=self.context).data
    
    def get_product_count(self, obj):
        """Get number of products in this category."""
        return obj.products.count()


class CategoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for category lists."""
    
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'parent', 'parent_name',
            'is_active', 'product_count', 'created_at'
        ]
    
    def get_product_count(self, obj):
        """Get number of products in this category."""
        return obj.products.count()


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_in_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'description', 'category', 'category_name',
            'price', 'stock_quantity', 'is_active', 'is_in_stock',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_in_stock(self, obj):
        """Check if product is in stock."""
        return obj.is_in_stock()
    
    def validate_price(self, value):
        """Validate price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value
    
    def validate_stock_quantity(self, value):
        """Validate stock quantity is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quantity',
            'purchase_price', 'total_price', 'created_at'
        ]
        read_only_fields = ['id', 'purchase_price', 'total_price', 'created_at']
    
    def get_total_price(self, obj):
        """Calculate total price for this order item."""
        return obj.get_total_price()
    
    def validate_quantity(self, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value
    
    def validate(self, attrs):
        """Validate order item data."""
        product = attrs.get('product')
        quantity = attrs.get('quantity')
        
        if product and quantity:
            if not product.is_in_stock():
                raise serializers.ValidationError(
                    f"Product '{product.name}' is out of stock."
                )
            if quantity > product.stock_quantity:
                raise serializers.ValidationError(
                    f"Requested quantity ({quantity}) exceeds available stock "
                    f"({product.stock_quantity}) for product '{product.name}'."
                )
        
        return attrs


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating OrderItem (without read-only fields)."""
    
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
    
    def validate_quantity(self, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model with nested items."""
    
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    can_be_cancelled = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'customer_name', 'customer_email', 'status',
            'total', 'items', 'item_count', 'can_be_cancelled',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total', 'created_at', 'updated_at']
    
    def get_item_count(self, obj):
        """Get total number of items in the order."""
        return obj.get_item_count()
    
    def get_can_be_cancelled(self, obj):
        """Check if order can be cancelled."""
        return obj.can_be_cancelled()


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Order with items."""
    
    items = OrderItemCreateSerializer(many=True)
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'items']
        extra_kwargs = {
            'customer': {'required': False}
        }
    
    def validate_items(self, value):
        """Validate order items."""
        if not value:
            raise serializers.ValidationError("Order must have at least one item.")
        
        # Check for duplicate products
        products = [item['product'] for item in value]
        if len(products) != len(set(products)):
            raise serializers.ValidationError("Duplicate products in order items.")
        
        # Check stock availability
        for item in value:
            product = item['product']
            quantity = item['quantity']
            if quantity > product.stock_quantity:
                raise serializers.ValidationError(
                    f"Quantity {quantity} for product '{product.name}' exceeds available stock ({product.stock_quantity})."
                )
        
        return value
    
    def create(self, validated_data):
        """Create order with items and calculate total."""
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            # Create order item (purchase_price will be set automatically)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                purchase_price=product.price
            )
            
            # Reduce stock
            product.reduce_stock(quantity)
        
        # Calculate total
        order.calculate_total()
        
        # TODO: Add hooks for SMS and email notifications
        # self._send_sms_notification(order)
        # self._send_admin_email(order)
        
        return order
    
    def _send_sms_notification(self, order):
        """Placeholder for SMS notification via Africa's Talking."""
        # TODO: Implement SMS notification
        pass
    
    def _send_admin_email(self, order):
        """Placeholder for admin email notification."""
        # TODO: Implement email notification
        pass


class CategoryAveragePriceSerializer(serializers.Serializer):
    """Serializer for category average price response."""
    
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    product_count = serializers.IntegerField()
    descendant_categories = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of descendant category names included in calculation"
    )
