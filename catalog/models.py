from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator
from django.utils import timezone
from decimal import Decimal
from mptt.models import MPTTModel, TreeForeignKey


class CustomerProfile(models.Model):
    """Customer profile extending Django User with additional information."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        help_text="Phone number in international format"
    )
    address = models.TextField(
        max_length=500,
        help_text="Customer's full address"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer Profiles"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.email})"


class Category(MPTTModel):
    """Hierarchical category model using django-mptt."""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def get_average_price(self):
        """Calculate average price of all products in this category and its descendants."""
        from django.db.models import Avg
        
        # Get all descendant categories including self
        descendants = self.get_descendants(include_self=True)
        
        # Calculate average price across all products in these categories
        avg_price = Product.objects.filter(
            category__in=descendants,
            is_active=True
        ).aggregate(avg_price=Avg('price'))['avg_price']
        
        return avg_price or Decimal('0.00')


class Product(models.Model):
    """Product model with category relationship and inventory tracking."""
    
    name = models.CharField(max_length=200)
    sku = models.CharField(
        max_length=50,
        unique=True,
        help_text="Stock Keeping Unit - unique product identifier"
    )
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Current stock quantity"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def is_in_stock(self):
        """Check if product is in stock."""
        return self.stock_quantity > 0

    def reduce_stock(self, quantity):
        """Reduce stock quantity by specified amount."""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.save()
            return True
        return False

    def add_stock(self, quantity):
        """Add stock quantity."""
        self.stock_quantity += quantity
        self.save()


class Order(models.Model):
    """Order model representing a customer's purchase."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.customer.get_full_name()} ({self.status})"

    def calculate_total(self):
        """Calculate total order amount from order items."""
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.get_total_price()
        
        self.total = total
        self.save()
        return total

    def get_item_count(self):
        """Get total number of items in the order."""
        return sum(item.quantity for item in self.items.all())

    def can_be_cancelled(self):
        """Check if order can be cancelled."""
        return self.status in ['pending', 'confirmed']


class OrderItem(models.Model):
    """Order item linking products to orders with quantity and pricing."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price at the time of purchase"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        unique_together = ['order', 'product']

    def __str__(self):
        return f"{self.product.name} x{self.quantity} - ${self.purchase_price}"

    def get_total_price(self):
        """Calculate total price for this order item."""
        return self.quantity * self.purchase_price

    def save(self, *args, **kwargs):
        """Override save to set purchase price from current product price."""
        if not self.purchase_price:
            self.purchase_price = self.product.price
        super().save(*args, **kwargs)
