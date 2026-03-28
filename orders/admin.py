# orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem, OrderTracking

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'price', 'quantity', 'subtotal']
    fields = ['product_name', 'price', 'quantity', 'subtotal']

class OrderTrackingInline(admin.TabularInline):
    model = OrderTracking
    extra = 0
    readonly_fields = ['created_at']
    fields = ['status', 'location', 'notes', 'created_at']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'order_number', 'user', 'status', 'payment_status', 
        'total', 'created_at', 'delivery_agent'
    ]
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__email', 'user__username', 'tracking_number']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'payment_method')
        }),
        ('Delivery Information', {
            'fields': ('delivery_address', 'delivery_phone', 'delivery_instructions', 'delivery_date', 'delivery_time_slot')
        }),
        ('Tracking', {
            'fields': ('tracking_number', 'delivery_agent', 'estimated_delivery', 'actual_delivery')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'delivery_fee', 'service_fee', 'discount', 'tax', 'total')
        }),
        ('Location', {
            'fields': ('current_location', 'location_lat', 'location_lng'),
            'classes': ('collapse',)
        }),
        ('Feedback', {
            'fields': ('customer_rating', 'customer_feedback', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [OrderItemInline, OrderTrackingInline]
    
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered']
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(payment_status='paid')
        self.message_user(request, f'{updated} order(s) marked as paid.')
    mark_as_paid.short_description = "Mark selected as paid"
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} order(s) marked as shipped.')
    mark_as_shipped.short_description = "Mark selected as shipped"
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f'{updated} order(s) marked as delivered.')
    mark_as_delivered.short_description = "Mark selected as delivered"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product_name', 'quantity', 'price', 'subtotal']
    list_filter = ['order__status']
    search_fields = ['product_name', 'order__order_number']
    readonly_fields = ['subtotal']

@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'status', 'location', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_number']