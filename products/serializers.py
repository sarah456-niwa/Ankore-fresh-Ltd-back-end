# products/serializers.py
from rest_framework import serializers
from .models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'product_count', 'is_active']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_name = serializers.CharField(read_only=True)
    formatted_price = serializers.CharField(read_only=True)
    availability_text = serializers.CharField(read_only=True)
    availability_color = serializers.CharField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'wholesale_price',
            'min_bulk_quantity', 'unit', 'image', 'image_url', 'stock',
            'rating', 'is_organic', 'is_featured', 'category', 'category_name',
            'seller', 'seller_name', 'formatted_price', 'availability_text',
            'availability_color', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['seller', 'rating']