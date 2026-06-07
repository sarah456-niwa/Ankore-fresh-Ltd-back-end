# orders/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from .models import Order, OrderItem, OrderTracking
from .serializers import OrderSerializer
from .websocket_utils import send_order_update_websocket, send_user_notification_websocket

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
        'order_number', 
        'customer_link', 
        'customer_phone_display',
        'status_colored', 
        'payment_status_colored', 
        'total_display',
        'delivery_info',
        'created_at'
    ]
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone', 'user__email', 'tracking_number']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'customer_name', 'customer_email', 'customer_phone', 'status', 'payment_status', 'payment_method')
        }),
        ('Delivery Information', {
            'fields': ('delivery_address', 'delivery_phone', 'delivery_instructions', 'notes', 'delivery_date', 'delivery_time_slot')
        }),
        ('Tracking', {
            'fields': ('tracking_number', 'delivery_agent', 'estimated_delivery', 'actual_delivery', 'current_location')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'delivery_fee', 'service_fee', 'discount', 'tax', 'total')
        }),
        ('Location', {
            'fields': ('location_lat', 'location_lng'),
            'classes': ('collapse',)
        }),
        ('Feedback', {
            'fields': ('customer_rating', 'customer_feedback'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [OrderItemInline, OrderTrackingInline]
    
    actions = ['mark_as_paid', 'mark_as_confirmed', 'mark_as_processing', 'mark_as_shipped', 'mark_as_out_for_delivery', 'mark_as_delivered']
    
    def customer_link(self, obj):
        if obj.customer_name:
            return format_html(
                '<strong>{}</strong><br><span style="color: #666; font-size: 11px;">{}</span>',
                obj.customer_name,
                obj.customer_email or 'No email'
            )
        return format_html(
            '<strong>{}</strong><br><span style="color: #666; font-size: 11px;">{}</span>',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    customer_link.short_description = 'Customer'
    
    def customer_phone_display(self, obj):
        phone = obj.customer_phone or str(obj.delivery_phone) if obj.delivery_phone else ''
        if phone:
            return format_html('<span style="font-family: monospace;">📞 {}</span>', phone)
        return '-'
    customer_phone_display.short_description = 'Phone'
    
    def delivery_info(self, obj):
        address = obj.delivery_address[:50] + '...' if len(obj.delivery_address) > 50 else obj.delivery_address
        return format_html(
            '<span style="font-size: 11px;">📍 {}</span>',
            address
        )
    delivery_info.short_description = 'Delivery Address'
    
    def status_colored(self, obj):
        colors = {
            'pending': '#ff9800',
            'confirmed': '#2196f3',
            'processing': '#9c27b0',
            'shipped': '#00bcd4',
            'out_for_delivery': '#ff5722',
            'delivered': '#4caf50',
            'cancelled': '#f44336',
            'refunded': '#795548',
        }
        color = colors.get(obj.status, '#666')
        return format_html('<span style="color: {}; font-weight: bold;">●</span> {}', color, obj.get_status_display())
    status_colored.short_description = 'Status'
    
    def payment_status_colored(self, obj):
        colors = {
            'pending': '#ff9800',
            'paid': '#4caf50',
            'failed': '#f44336',
            'refunded': '#795548',
        }
        color = colors.get(obj.payment_status, '#666')
        return format_html('<span style="color: {}; font-weight: bold;">●</span> {}', color, obj.get_payment_status_display())
    payment_status_colored.short_description = 'Payment'
    
    def total_display(self, obj):
        # FIXED: Proper formatting for currency
        return f"UGX {obj.total:,.0f}"
    total_display.short_description = 'Total'
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(payment_status='paid')
        self.message_user(request, f'{updated} order(s) marked as paid.')
    mark_as_paid.short_description = "✅ Mark selected as Paid"
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        for order in queryset:
            self._send_status_update(order, 'confirmed')
        self.message_user(request, f'{updated} order(s) marked as confirmed.')
    mark_as_confirmed.short_description = "✓ Mark selected as Confirmed"
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        for order in queryset:
            self._send_status_update(order, 'processing')
        self.message_user(request, f'{updated} order(s) marked as processing.')
    mark_as_processing.short_description = "🔧 Mark selected as Processing"
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        for order in queryset:
            self._send_status_update(order, 'shipped')
        self.message_user(request, f'{updated} order(s) marked as shipped.')
    mark_as_shipped.short_description = "📦 Mark selected as Shipped"
    
    def mark_as_out_for_delivery(self, request, queryset):
        updated = queryset.update(status='out_for_delivery')
        for order in queryset:
            self._send_status_update(order, 'out_for_delivery')
        self.message_user(request, f'{updated} order(s) marked as out for delivery.')
    mark_as_out_for_delivery.short_description = "🚚 Mark selected as Out for Delivery"
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered', actual_delivery=timezone.now())
        for order in queryset:
            self._send_status_update(order, 'delivered')
        self.message_user(request, f'{updated} order(s) marked as delivered.')
    mark_as_delivered.short_description = "🏠 Mark selected as Delivered"
    
    def _send_status_update(self, order, new_status):
        """Trigger notification when status changes via admin action"""
        from django.core.mail import send_mail
        from django.conf import settings
        from notifications.models import Notification as UserNotification
        
        # Create tracking entry
        OrderTracking.objects.create(
            order=order,
            status=new_status,
            notes=f"Status updated to {order.get_status_display()} by admin"
        )
        
        # Create in-app notification for the user
        UserNotification.objects.create(
            user=order.user,
            title=f"Order {new_status.replace('_', ' ').title()}",
            message=f"Your order #{order.order_number} status has been updated to: {order.get_status_display()}",
            notification_type='delivery',
            data={'order_id': order.id, 'status': new_status}
        )
        # Send in-app websocket notification to user to trigger UI badge
        try:
            latest = UserNotification.objects.filter(user=order.user).first()
            if latest:
                send_user_notification_websocket(order.user.id, latest.id, latest.message, notification_type='order_update')
        except Exception:
            pass
        
        # Send WebSocket update to all connected clients
        serializer = OrderSerializer(order)
        send_order_update_websocket(order.order_number, serializer.data)
        
        # Send email notification to customer
        if order.customer_email:
            subject = f"Order Update - {order.order_number}"
            message = f"""
Dear {order.customer_name or 'Customer'},

Your order #{order.order_number} status has been updated to: {order.get_status_display()}

Order Details:
- Order Number: {order.order_number}
- Status: {order.get_status_display()}
- Total: UGX {order.total:,.0f}

Track your order: {settings.SITE_URL}/track/{order.order_number}

Thank you for shopping with Ankore Fresh!
"""
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.customer_email],
                    fail_silently=True,
                )
                print(f"📧 Status update email sent to {order.customer_email}")
            except Exception as e:
                print(f"Failed to send email: {e}")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def save_model(self, request, obj, form, change):
        if change:
            # Check if status changed
            original = Order.objects.get(id=obj.id)
            if original.status != obj.status:
                # Create tracking entry
                OrderTracking.objects.create(
                    order=obj,
                    status=obj.status,
                    notes=f"Status updated from {original.get_status_display()} to {obj.get_status_display()} by admin"
                )
                
                # Create in-app notification for the user
                from notifications.models import Notification as UserNotification
                UserNotification.objects.create(
                    user=obj.user,
                    title=f"Order {obj.status.replace('_', ' ').title()}",
                    message=f"Your order #{obj.order_number} status has been updated to: {obj.get_status_display()}",
                    notification_type='delivery',
                    data={'order_id': obj.id, 'status': obj.status}
                )
                # Notify user via websocket badge
                try:
                    latest = UserNotification.objects.filter(user=obj.user).first()
                    if latest:
                        send_user_notification_websocket(obj.user.id, latest.id, latest.message, notification_type='order_update')
                except Exception:
                    pass
                
                # Send WebSocket update to all connected clients
                serializer = OrderSerializer(obj)
                send_order_update_websocket(obj.order_number, serializer.data)
        super().save_model(request, obj, form, change)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_link', 'product_name', 'quantity', 'price', 'subtotal']
    list_filter = ['order__status']
    search_fields = ['product_name', 'order__order_number']
    readonly_fields = ['subtotal']
    
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">#{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Order'

@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_link', 'status_colored', 'location', 'notes', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_number']
    readonly_fields = ['created_at']
    
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">#{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Order'
    
    def status_colored(self, obj):
        colors = {
            'pending': '#ff9800',
            'confirmed': '#2196f3',
            'processing': '#9c27b0',
            'shipped': '#00bcd4',
            'out_for_delivery': '#ff5722',
            'delivered': '#4caf50',
            'cancelled': '#f44336',
            'refunded': '#795548',
        }
        color = colors.get(obj.status, '#666')
        return format_html('<span style="color: {}; font-weight: bold;">●</span> {}', color, obj.get_status_display())
    status_colored.short_description = 'Status'