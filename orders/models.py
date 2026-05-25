from django.db import models
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
import random
from decimal import Decimal

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash on Delivery'),
        ('momo', 'MTN Mobile Money'),
        ('airtel', 'Airtel Money'),
        ('card', 'Credit/Debit Card'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    
    # Customer details
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Delivery info
    delivery_address = models.TextField()
    delivery_phone = PhoneNumberField(region='UG')
    delivery_instructions = models.TextField(blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    delivery_time_slot = models.CharField(max_length=50, blank=True)
    pickup_location = models.CharField(max_length=255, blank=True)
    
    # Location tracking
    current_location = models.CharField(max_length=255, blank=True)
    location_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=0, default=5000)
    service_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    
    # Tracking
    tracking_number = models.CharField(max_length=50, blank=True)
    delivery_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='deliveries', limit_choices_to={'user_type': 'delivery'}
    )
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    
    # Notes and feedback
    notes = models.TextField(blank=True)
    customer_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    customer_feedback = models.TextField(blank=True)
    
    # Notification tracking
    email_notification_sent = models.BooleanField(default=False)
    sms_notification_sent = models.BooleanField(default=False)
    email_notification_sent_at = models.DateTimeField(blank=True, null=True)
    sms_notification_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Admin notification tracking
    is_admin_notified = models.BooleanField(default=False)
    admin_notification_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    @property
    def can_cancel(self):
        return self.status in ['pending', 'confirmed']
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def get_payment_status_display(self):
        return dict(self.PAYMENT_STATUS_CHOICES).get(self.payment_status, self.payment_status)
    
    def get_payment_method_display(self):
        return dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, self.payment_method)
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ANK-{random.randint(100000, 999999)}"
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='order_items')
    product_name = models.CharField(max_length=200)
    product_image = models.CharField(max_length=500, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=0)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

class OrderTracking(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.status}"
    
    def get_status_display(self):
        return dict(Order.STATUS_CHOICES).get(self.status, self.status)

class OrderNotification(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='admin_notifications')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order Notification'
        verbose_name_plural = 'Order Notifications'
    
    def __str__(self):
        return f"Notification for {self.order.order_number}"