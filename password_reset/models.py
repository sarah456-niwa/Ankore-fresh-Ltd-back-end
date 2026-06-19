from django.db import models
from django.conf import settings
import random
import string

class PasswordResetToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        from django.utils import timezone
        from datetime import timedelta
        return not self.is_used and (timezone.now() - self.created_at) < timedelta(minutes=15)
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = ''.join(random.choices(string.digits, k=6))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Password reset for {self.email} - {self.token}"