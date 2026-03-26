from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('immediate', 'Immediate Buyer'),
        ('bulk', 'Bulk Buyer/Seller'),
        ('admin', 'Admin'),
        ('delivery', 'Delivery Agent'),
    )
    
    # Authentication fields
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(region='UG', blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='immediate')
    
    # Business fields for bulk sellers
    store_name = models.CharField(max_length=255, blank=True, null=True)
    business_address = models.TextField(blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    is_verified_seller = models.BooleanField(default=False)
    
    # Profile fields
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Location tracking (for delivery)
    current_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    @property
    def name(self):
        """Match Flutter's 'name' field"""
        return self.get_full_name() or self.email.split('@')[0]
    
    @property
    def is_bulk_buyer(self):
        return self.user_type == 'bulk'
    
    @property
    def is_immediate_buyer(self):
        return self.user_type == 'immediate'
    
    @property
    def can_sell(self):
        return self.is_bulk_buyer and self.is_verified_seller