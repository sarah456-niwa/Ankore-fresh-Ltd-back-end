from rest_framework import serializers
from .models import Order, OrderItem, OrderTracking
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

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    tracking_history = OrderTrackingSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display', 'payment_status',
            'payment_status_display', 'payment_method', 'payment_method_display',
            'delivery_address', 'delivery_phone', 'delivery_instructions',
            'delivery_date', 'delivery_time_slot', 'pickup_location',
            'current_location', 'location_lat', 'location_lng',
            'subtotal', 'delivery_fee', 'service_fee', 'discount', 'tax', 'total',
            'tracking_number', 'delivery_agent', 'estimated_delivery', 'actual_delivery',
            'notes', 'customer_rating', 'customer_feedback', 'can_cancel',
            'items', 'tracking_history', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'created_at', 'updated_at']

class OrderCreateSerializer(serializers.Serializer):
    cart_id = serializers.IntegerField(required=False)
    delivery_address = serializers.CharField()
    delivery_phone = serializers.CharField()
    delivery_instructions = serializers.CharField(required=False, allow_blank=True)
    delivery_date = serializers.DateTimeField(required=False)
    delivery_time_slot = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_delivery_phone(self, value):
        import re
        ug_phone_pattern = r'^(\+256|0)[0-9]{9}$'
        if not re.match(ug_phone_pattern, value):
            raise serializers.ValidationError("Enter a valid Ugandan phone number")
        return value

class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    location = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)