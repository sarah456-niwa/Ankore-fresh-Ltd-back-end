from rest_framework import serializers
from .models import Order, OrderItem, OrderTracking, OrderNotification
from products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_details', 'product_name', 'product_image', 'price', 'quantity', 'subtotal']
        read_only_fields = ['product_name', 'product_image', 'price', 'subtotal']

class OrderTrackingSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = OrderTracking
        fields = ['id', 'status', 'status_display', 'location', 'notes', 'created_at']

class OrderNotificationSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    customer_name = serializers.CharField(source='order.customer_name', read_only=True)
    
    class Meta:
        model = OrderNotification
        fields = ['id', 'order', 'order_number', 'customer_name', 'is_read', 'read_at', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    tracking_history = OrderTrackingSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'

class OrderCreateSerializer(serializers.Serializer):
    # Customer details
    customer_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    customer_email = serializers.EmailField(required=False, allow_null=True)
    customer_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    # Delivery details
    delivery_address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    delivery_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    delivery_instructions = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    payment_method = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    # Cart items
    items = serializers.ListField(required=False, child=serializers.DictField())
    
    # Optional fields from Flutter
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=0, required=False, allow_null=True)
    delivery_fee = serializers.DecimalField(max_digits=10, decimal_places=0, required=False, allow_null=True)
    service_fee = serializers.DecimalField(max_digits=10, decimal_places=0, required=False, allow_null=True)
    tax = serializers.DecimalField(max_digits=10, decimal_places=0, required=False, allow_null=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=0, required=False, allow_null=True)
    
    def validate_payment_method(self, value):
        if not value:
            return 'cash'
        valid_methods = ['cash', 'momo', 'airtel', 'card']
        return value.lower() if value.lower() in valid_methods else 'cash'

class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    location = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)