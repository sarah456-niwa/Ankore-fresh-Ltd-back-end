# products/admin.py
from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'product_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'name': ('name',)}
    
    def product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    product_count.short_description = 'Products'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'category', 'price', 'unit', 'stock', 
        'rating', 'is_organic', 'is_featured', 'is_active', 'created_at'
    ]
    list_filter = ['category', 'is_organic', 'is_featured', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock', 'is_organic', 'is_featured', 'is_active']
    readonly_fields = ['rating', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'unit')
        }),
        ('Pricing', {
            'fields': ('price',)
        }),
        ('Inventory', {
            'fields': ('stock',)
        }),
        ('Media', {
            'fields': ('image', 'image_url')
        }),
        ('Flags', {
            'fields': ('is_organic', 'is_featured', 'is_active')
        }),
        ('Ratings', {
            'fields': ('rating',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )