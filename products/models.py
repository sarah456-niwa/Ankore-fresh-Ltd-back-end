# products/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    # Seller info (null = main store)
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='products',
        null=True, 
        blank=True,
        limit_choices_to={'user_type': 'bulk', 'is_verified_seller': True}
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    
    # Basic info
    name = models.CharField(max_length=200)
    description = models.TextField()
    unit = models.CharField(max_length=50, help_text="e.g., per kg, per bunch, each")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=0)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    min_bulk_quantity = models.PositiveIntegerField(default=1)
    
    # Media
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True)
    
    # Stock and ratings
    stock = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    
    # Flags
    is_organic = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def formatted_price(self):
        return f"UGX {self.price}"
    
    @property
    def is_available(self):
        return self.stock > 0 and self.is_active
    
    @property
    def availability_text(self):
        if self.stock > 10:
            return 'In Stock'
        elif self.stock > 0:
            return f'Low Stock ({self.stock} left)'
        return 'Out of Stock'
    
    @property
    def availability_color(self):
        if self.stock > 10:
            return 'green'
        elif self.stock > 0:
            return 'orange'
        return 'red'
    
    @property
    def seller_name(self):
        if self.seller:
            return self.seller.store_name or self.seller.name
        return "Ankore Fresh"