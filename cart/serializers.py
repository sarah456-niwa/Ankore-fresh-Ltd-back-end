from rest_framework import serializers
from .models import CartItem
from products.models import Product
from products.serializers import ProductSerializer
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(source='product', queryset=Product.objects.all(), write_only=True)
    class Meta:
        model = CartItem
        fields = ('id','product','product_id','quantity','added_at')
        read_only_fields = ('id','added_at','product')
    def validate_quantity(self, v):
        if v<=0: raise serializers.ValidationError("Quantity must be positive.")
        return v
