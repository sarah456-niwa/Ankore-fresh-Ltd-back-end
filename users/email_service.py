import logging

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)


def send_welcome_email(user):
    """Send welcome email with CTA buttons to new user.

    Returns True if sending succeeded, False otherwise.
    """
    try:
        context = {
            'user_name': user.get_full_name() or user.email,
            'email': user.email,
            'shop_url': f"{settings.SITE_URL}/products",
            'user_type': getattr(user, 'get_user_type_display', lambda: '')(),
        }

        subject = f"Welcome to Ankore Fresh, {context['user_name']}!"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px 20px; }}
                .welcome-text {{ font-size: 16px; margin-bottom: 20px; }}
                .cta-buttons {{ display: flex; gap: 15px; margin-top: 30px; justify-content: center; flex-wrap: wrap; }}
                .btn {{ display: inline-block; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; border: none; cursor: pointer; }}
                .btn-primary {{ background-color: #4CAF50; color: white; }}
                .footer {{ background-color: #333; color: white; padding: 15px; text-align: center; font-size: 12px; border-radius: 0 0 5px 5px; }}
                .footer a {{ color: #4CAF50; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🥬 Ankore Fresh 🥬</h1>
                </div>
                <div class="content">
                    <div class="welcome-text">
                        <p>Hello <strong>{context['user_name']}</strong>,</p>
                        <p>Thank you for registering with Ankore Fresh! Your account has been created successfully.</p>
                        <p><strong>Account Type:</strong> {context['user_type']}</p>
                        <p>You can now start shopping for fresh produce directly from us.</p>
                    </div>
                    <div class="cta-buttons">
                        <a href="{context['shop_url']}" class="btn btn-primary" style="display: inline-block; text-decoration: none;">🛒 Shop with Us</a>
                    </div>
                </div>
                <div class="footer">
                    <p>© 2026 Ankore Fresh Ltd. All rights reserved.</p>
                    <p><a href="{settings.SITE_URL}">Visit our website</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = (
            f"Welcome to Ankore Fresh, {context['user_name']}!\n\n"
            f"Thank you for registering with Ankore Fresh! Your account has been created successfully.\n\n"
            f"Account Type: {context['user_type']}\n\n"
            f"Shop with Us: {context['shop_url']}\n\n"
            "Contact Support: support@ankorefresh.com\n\n"
            "© 2026 Ankore Fresh Ltd. All rights reserved."
        )

        msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info("Welcome email sent to %s", user.email)
        return True

    except Exception as e:
        logger.exception("Failed to send welcome email to %s: %s", getattr(user, 'email', '<unknown>'), e)
        return False


def send_password_reset_email(user, code):
    """Send a short OTP code to user's email. Returns True on success.

    Falls back to logging/printing in development when SMTP isn't configured.
    """
    try:
        subject = "Your Ankore Fresh password reset code"
        text_content = (
            f"Your Ankore Fresh password reset code is: {code}\n\n"
            "This code expires in 15 minutes. If you did not request a password reset, ignore this message."
        )

        html_content = f"<p>Your Ankore Fresh password reset code is: <strong>{code}</strong></p><p>This code expires in 15 minutes.</p>"

        msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info("Password reset email sent to %s", user.email)
        return True
    except Exception as e:
        logger.exception("Failed to send password reset email to %s: %s", getattr(user, 'email', '<unknown>'), e)
        # dev fallback
        try:
            print(f"📧 Password reset email to {getattr(user,'email', '<unknown>')}: code={code}")
        except Exception:
            pass
        return False
