from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg, Sum
from django.urls import reverse
from django.utils.safestring import mark_safe
from mptt.admin import MPTTModelAdmin
from .models import CustomerProfile, Category, Product, Order, OrderItem

# Customize admin site header and title
admin.site.site_header = "TechMart Admin"
admin.site.site_title = "TechMart Admin Portal"
admin.site.index_title = "Welcome to TechMart Administration"

# Add custom CSS to admin site
admin.site.enable_nav_sidebar = True

# Customize admin site appearance
admin.site.site_url = None  # Remove "View site" link
admin.site.empty_value_display = '-'

# Base admin class with custom CSS
class CustomAdminMixin:
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(CustomerProfile)
class CustomerProfileAdmin(CustomAdminMixin, admin.ModelAdmin):
    """Admin interface for CustomerProfile model."""
    
    list_display = ['user_link', 'phone', 'address_preview', 'order_count', 'created_at']
    list_filter = ['created_at', 'updated_at', 'user__is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'order_count_display']
    list_per_page = 25
    
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'order_count_display'),
            'classes': ('wide',)
        }),
        ('Contact Information', {
            'fields': ('phone', 'address'),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        """Display user as a clickable link."""
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__first_name'
    
    def address_preview(self, obj):
        """Display truncated address."""
        if len(obj.address) > 50:
            return obj.address[:50] + '...'
        return obj.address
    address_preview.short_description = 'Address'
    
    def order_count(self, obj):
        """Display number of orders for this customer."""
        count = obj.user.orders.count()
        if count > 0:
            url = reverse('admin:catalog_order_changelist') + '?customer__id__exact={}'.format(obj.user.id)
            return format_html('<a href="{}" style="color: #417690; font-weight: bold;">{} orders</a>', url, count)
        return '0 orders'
    order_count.short_description = 'Orders'
    
    def order_count_display(self, obj):
        """Display order count in detail view."""
        count = obj.user.orders.count()
        if count > 0:
            url = reverse('admin:catalog_order_changelist') + '?customer__id__exact={}'.format(obj.user.id)
            return format_html('<a href="{}" style="color: #417690; font-weight: bold;">{} orders</a>', url, count)
        return 'No orders yet'
    order_count_display.short_description = 'Total Orders'


@admin.register(Category)
class CategoryAdmin(CustomAdminMixin, MPTTModelAdmin):
    """Admin interface for Category model with MPTT support."""
    
    list_display = ['name', 'slug', 'parent', 'is_active_badge', 'product_count', 'avg_price', 'created_at']
    list_filter = ['is_active', 'created_at', 'parent']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'product_count_display', 'avg_price_display']
    list_per_page = 25
    
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'slug', 'description', 'parent'),
            'classes': ('wide',)
        }),
        ('Statistics', {
            'fields': ('product_count_display', 'avg_price_display'),
            'classes': ('wide',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active_badge(self, obj):
        """Display active status as a colored badge."""
        if obj.is_active:
            return format_html('<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">ACTIVE</span>')
        else:
            return format_html('<span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">INACTIVE</span>')
    is_active_badge.short_description = 'Status'
    is_active_badge.admin_order_field = 'is_active'
    
    def product_count(self, obj):
        """Display number of products in this category with link."""
        count = obj.products.count()
        if count > 0:
            url = reverse('admin:catalog_product_changelist') + '?category__id__exact={}'.format(obj.id)
            return format_html('<a href="{}" style="color: #417690; font-weight: bold;">{} products</a>', url, count)
        return '0 products'
    product_count.short_description = 'Products'
    
    def product_count_display(self, obj):
        """Display product count in detail view."""
        count = obj.products.count()
        if count > 0:
            url = reverse('admin:catalog_product_changelist') + '?category__id__exact={}'.format(obj.id)
            return format_html('<a href="{}" style="color: #417690; font-weight: bold;">{} products</a>', url, count)
        return 'No products in this category'
    product_count_display.short_description = 'Total Products'
    
    def avg_price(self, obj):
        """Display average price of products in this category."""
        try:
            avg = obj.get_average_price()
            # Handle None, SafeString, or invalid values
            if avg is None:
                return 'N/A'
            
            # Convert to float, handling SafeString and other types
            avg_float = float(str(avg))
            
            if avg_float > 0:
                return format_html('<span style="color: #28a745; font-weight: bold;">${:.2f}</span>', avg_float)
            else:
                return 'N/A'
        except (ValueError, TypeError, AttributeError):
            return 'N/A'
    avg_price.short_description = 'Average Price'
    
    def avg_price_display(self, obj):
        """Display average price in detail view."""
        try:
            avg = obj.get_average_price()
            # Handle None, SafeString, or invalid values
            if avg is None:
                return 'No products to calculate average'
            
            # Convert to float, handling SafeString and other types
            avg_float = float(str(avg))
            
            if avg_float > 0:
                return format_html('<span style="color: #28a745; font-weight: bold; font-size: 16px;">${:.2f}</span>', avg_float)
            else:
                return 'No products to calculate average'
        except (ValueError, TypeError, AttributeError):
            return 'No products to calculate average'
    avg_price_display.short_description = 'Average Product Price'


@admin.register(Product)
class ProductAdmin(CustomAdminMixin, admin.ModelAdmin):
    """Admin interface for Product model."""
    
    list_display = ['name', 'sku', 'category_link', 'price', 'stock_quantity', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'created_at', 'stock_quantity']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = ['created_at', 'updated_at', 'stock_status_display', 'order_count_display']
    list_per_page = 25
    list_editable = ['price', 'stock_quantity', 'is_active']
    
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'sku', 'description', 'category'),
            'classes': ('wide',)
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock_quantity', 'stock_status_display'),
            'classes': ('wide',)
        }),
        ('Statistics', {
            'fields': ('order_count_display',),
            'classes': ('wide',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def category_link(self, obj):
        """Display category as a clickable link."""
        url = reverse('admin:catalog_category_change', args=[obj.category.pk])
        return format_html('<a href="{}">{}</a>', url, obj.category.name)
    category_link.short_description = 'Category'
    category_link.admin_order_field = 'category__name'
    
    def price_formatted(self, obj):
        """Display price with currency formatting."""
        try:
            if obj.price is None:
                return 'N/A'
            
            # Convert to float, handling SafeString and other types
            price_float = float(str(obj.price))
            return format_html('<span style="color: #28a745; font-weight: bold;">${:.2f}</span>', price_float)
        except (ValueError, TypeError, AttributeError):
            return 'N/A'
    price_formatted.short_description = 'Price'
    price_formatted.admin_order_field = 'price'
    
    def stock_status(self, obj):
        """Display stock status with color coding."""
        if obj.stock_quantity == 0:
            return format_html('<span style="color: #dc3545; font-weight: bold;">OUT OF STOCK</span>')
        elif obj.stock_quantity < 10:
            return format_html('<span style="color: #ffc107; font-weight: bold;">LOW STOCK ({})</span>', str(obj.stock_quantity))
        else:
            return format_html('<span style="color: #28a745; font-weight: bold;">IN STOCK ({})</span>', str(obj.stock_quantity))
    stock_status.short_description = 'Stock'
    stock_status.admin_order_field = 'stock_quantity'
    
    def stock_status_display(self, obj):
        """Display stock status in detail view."""
        if obj.stock_quantity == 0:
            return format_html('<span style="color: #dc3545; font-weight: bold; font-size: 16px;">OUT OF STOCK</span>')
        elif obj.stock_quantity < 10:
            return format_html('<span style="color: #ffc107; font-weight: bold; font-size: 16px;">LOW STOCK - {} units remaining</span>', str(obj.stock_quantity))
        else:
            return format_html('<span style="color: #28a745; font-weight: bold; font-size: 16px;">IN STOCK - {} units available</span>', str(obj.stock_quantity))
    stock_status_display.short_description = 'Stock Status'
    
    def is_active_badge(self, obj):
        """Display active status as a colored badge."""
        if obj.is_active:
            return format_html('<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">ACTIVE</span>')
        else:
            return format_html('<span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">INACTIVE</span>')
    is_active_badge.short_description = 'Status'
    is_active_badge.admin_order_field = 'is_active'
    
    def order_count_display(self, obj):
        """Display number of times this product has been ordered."""
        count = obj.order_items.count()
        if count > 0:
            url = reverse('admin:catalog_orderitem_changelist') + '?product__id__exact={}'.format(obj.id)
            return format_html('<a href="{}" style="color: #417690; font-weight: bold;">Ordered {} times</a>', url, count)
        return 'Never ordered'
    order_count_display.short_description = 'Order History'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('category')


class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItem model."""
    
    model = OrderItem
    extra = 0
    readonly_fields = ['purchase_price', 'created_at', 'total_price_display']
    fields = ['product', 'quantity', 'purchase_price', 'total_price_display', 'created_at']
    
    def total_price_display(self, obj):
        """Display total price for this order item."""
        if obj.pk:
            try:
                total = obj.get_total_price()
                if total is None:
                    return 'N/A'
                
                # Convert to float, handling SafeString and other types
                total_float = float(str(total))
                return format_html('<span style="color: #28a745; font-weight: bold;">${:.2f}</span>', total_float)
            except (ValueError, TypeError, AttributeError):
                return 'N/A'
        return 'N/A'
    total_price_display.short_description = 'Total'


@admin.register(Order)
class OrderAdmin(CustomAdminMixin, admin.ModelAdmin):
    """Admin interface for Order model."""
    
    list_display = ['id', 'customer_link', 'status_badge', 'total_formatted', 'item_count', 'created_at']
    list_filter = ['status', 'created_at', 'customer']
    search_fields = ['customer__first_name', 'customer__last_name', 'customer__email']
    readonly_fields = ['total', 'created_at', 'updated_at', 'item_count_display']
    inlines = [OrderItemInline]
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    
    fieldsets = (
        ('Order Information', {
            'fields': ('customer', 'status'),
            'classes': ('wide',)
        }),
        ('Order Summary', {
            'fields': ('total', 'item_count_display'),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_link(self, obj):
        """Display customer as a clickable link."""
        url = reverse('admin:auth_user_change', args=[obj.customer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.customer.get_full_name() or obj.customer.username)
    customer_link.short_description = 'Customer'
    customer_link.admin_order_field = 'customer__first_name'
    
    def status_badge(self, obj):
        """Display order status as a colored badge."""
        status_colors = {
            'pending': '#ffc107',
            'confirmed': '#17a2b8',
            'processing': '#007bff',
            'shipped': '#6f42c1',
            'delivered': '#28a745',
            'cancelled': '#dc3545',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px; text-transform: uppercase;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def total_formatted(self, obj):
        """Display total with currency formatting."""
        try:
            if obj.total is None:
                return 'N/A'
            
            # Convert to float, handling SafeString and other types
            total_float = float(str(obj.total))
            return format_html('<span style="color: #28a745; font-weight: bold; font-size: 14px;">${:.2f}</span>', total_float)
        except (ValueError, TypeError, AttributeError):
            return 'N/A'
    total_formatted.short_description = 'Total'
    total_formatted.admin_order_field = 'total'
    
    def item_count(self, obj):
        """Display total number of items in the order."""
        count = obj.get_item_count()
        return format_html('<span style="font-weight: bold;">{} items</span>', count)
    item_count.short_description = 'Items'
    
    def item_count_display(self, obj):
        """Display item count in detail view."""
        count = obj.get_item_count()
        return format_html('<span style="font-weight: bold; font-size: 16px;">{} items</span>', count)
    item_count_display.short_description = 'Total Items'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related."""
        return super().get_queryset(request).select_related('customer').prefetch_related('items')
    
    def save_model(self, request, obj, form, change):
        """Recalculate total when saving order."""
        super().save_model(request, obj, form, change)
        obj.calculate_total()


@admin.register(OrderItem)
class OrderItemAdmin(CustomAdminMixin, admin.ModelAdmin):
    """Admin interface for OrderItem model."""
    
    list_display = ['order_link', 'product_link', 'quantity', 'purchase_price_formatted', 'total_price_formatted', 'created_at']
    list_filter = ['created_at', 'order__status', 'order__customer']
    search_fields = ['order__customer__first_name', 'order__customer__last_name', 'product__name', 'product__sku']
    readonly_fields = ['created_at', 'total_price_display']
    list_per_page = 25
    
    
    fieldsets = (
        ('Order Item Information', {
            'fields': ('order', 'product', 'quantity', 'purchase_price'),
            'classes': ('wide',)
        }),
        ('Pricing', {
            'fields': ('total_price_display',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def order_link(self, obj):
        """Display order as a clickable link."""
        url = reverse('admin:catalog_order_change', args=[obj.order.pk])
        return format_html('<a href="{}">Order #{}</a>', url, obj.order.id)
    order_link.short_description = 'Order'
    order_link.admin_order_field = 'order__id'
    
    def product_link(self, obj):
        """Display product as a clickable link."""
        url = reverse('admin:catalog_product_change', args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_link.short_description = 'Product'
    product_link.admin_order_field = 'product__name'
    
    def purchase_price_formatted(self, obj):
        """Display purchase price with currency formatting."""
        try:
            if obj.purchase_price is None:
                return 'N/A'
            
            # Convert to float, handling SafeString and other types
            price_float = float(str(obj.purchase_price))
            return format_html('<span style="color: #6c757d;">${:.2f}</span>', price_float)
        except (ValueError, TypeError, AttributeError):
            return 'N/A'
    purchase_price_formatted.short_description = 'Unit Price'
    purchase_price_formatted.admin_order_field = 'purchase_price'
    
    def total_price_formatted(self, obj):
        """Display total price for this order item."""
        try:
            total = obj.get_total_price()
            if total is None:
                return 'N/A'
            
            # Convert to float, handling SafeString and other types
            total_float = float(str(total))
            return format_html('<span style="color: #28a745; font-weight: bold;">${:.2f}</span>', total_float)
        except (ValueError, TypeError, AttributeError):
            return 'N/A'
    total_price_formatted.short_description = 'Total Price'
    
    def total_price_display(self, obj):
        """Display total price in detail view."""
        try:
            total = obj.get_total_price()
            if total is None:
                return 'N/A'
            
            # Convert to float, handling SafeString and other types
            total_float = float(str(total))
            return format_html('<span style="color: #28a745; font-weight: bold; font-size: 16px;">${:.2f}</span>', total_float)
        except (ValueError, TypeError, AttributeError):
            return 'N/A'
    total_price_display.short_description = 'Total Price'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('order', 'product', 'order__customer')
