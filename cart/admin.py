# cart/admin.py
from django.contrib import admin
from .models import Cart, CartItem

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_items', 'total_quantity', 'total_amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Items'
    
    def total_quantity(self, obj):
        return obj.total_quantity
    total_quantity.short_description = 'Quantity'
    
    def total_amount(self, obj):
        return f"UGX {obj.total_amount}"
    total_amount.short_description = 'Total'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'quantity', 'price_at_add', 'subtotal', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name', 'cart__user__email']
    readonly_fields = ['price_at_add', 'created_at']
    
    def subtotal(self, obj):
        return f"UGX {obj.subtotal}"
    subtotal.short_description = 'Subtotal'