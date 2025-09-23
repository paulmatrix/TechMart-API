from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from mptt.admin import MPTTModelAdmin
from .models import CustomerProfile, Category, Product, Order, OrderItem


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    """Admin interface for CustomerProfile model."""
    
    list_display = ['user', 'phone', 'address', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Contact Information', {
            'fields': ('phone', 'address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    """Admin interface for Category model with MPTT support."""
    
    list_display = ['name', 'slug', 'parent', 'is_active', 'product_count', 'created_at']
    list_filter = ['is_active', 'created_at', 'parent']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    def product_count(self, obj):
        """Display number of products in this category."""
        return obj.products.count()
    product_count.short_description = 'Products'
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin interface for Product model."""
    
    list_display = ['name', 'sku', 'category', 'price', 'stock_quantity', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'created_at', 'price']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'sku', 'description', 'category')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock_quantity')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('category')


class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItem model."""
    
    model = OrderItem
    extra = 0
    readonly_fields = ['purchase_price', 'created_at']
    fields = ['product', 'quantity', 'purchase_price', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order model."""
    
    list_display = ['id', 'customer', 'status', 'total', 'item_count', 'created_at']
    list_filter = ['status', 'created_at', 'customer']
    search_fields = ['customer__first_name', 'customer__last_name', 'customer__email']
    readonly_fields = ['total', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('customer', 'status')
        }),
        ('Totals', {
            'fields': ('total',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def item_count(self, obj):
        """Display total number of items in the order."""
        return obj.get_item_count()
    item_count.short_description = 'Items'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related."""
        return super().get_queryset(request).select_related('customer').prefetch_related('items')
    
    def save_model(self, request, obj, form, change):
        """Recalculate total when saving order."""
        super().save_model(request, obj, form, change)
        obj.calculate_total()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin interface for OrderItem model."""
    
    list_display = ['order', 'product', 'quantity', 'purchase_price', 'total_price', 'created_at']
    list_filter = ['created_at', 'order__status']
    search_fields = ['order__customer__first_name', 'order__customer__last_name', 'product__name', 'product__sku']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Order Item Information', {
            'fields': ('order', 'product', 'quantity', 'purchase_price')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def total_price(self, obj):
        """Display total price for this order item."""
        return f"${obj.get_total_price()}"
    total_price.short_description = 'Total Price'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('order', 'product')
