from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from .email_service import send_welcome_email

@receiver(post_save, sender=User)
def send_welcome_email_on_registration(sender, instance, created, **kwargs):
    """Send welcome email when a new user registers"""
    if created and instance.is_active:
        send_welcome_email(instance)
