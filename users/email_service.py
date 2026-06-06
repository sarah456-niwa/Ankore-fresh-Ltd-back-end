from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags

def send_welcome_email(user):
    """Send welcome email with CTA buttons to new user"""
    try:
        # Email context
        context = {
            'user_name': user.get_full_name() or user.email,
            'email': user.email,
            'shop_url': f"{settings.SITE_URL}/products",
            'user_type': user.get_user_type_display(),
        }
        
        # Create email subject
        subject = f"Welcome to Ankore Fresh, {context['user_name']}!"
        
        # HTML content with buttons
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
                .header h1 {{ margin: 0; font-size: 28px; }}
                .content {{ background-color: #f9f9f9; padding: 30px 20px; }}
                .welcome-text {{ font-size: 16px; margin-bottom: 20px; }}
                .cta-buttons {{ display: flex; gap: 15px; margin-top: 30px; justify-content: center; flex-wrap: wrap; }}
                .btn {{ display: inline-block; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; border: none; cursor: pointer; }}
                .btn-primary {{ background-color: #4CAF50; color: white; }}
                .btn-primary:hover {{ background-color: #45a049; }}
                .btn-secondary {{ background-color: #f44336; color: white; }}
                .btn-secondary:hover {{ background-color: #da190b; }}
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
                        <p>You can now start shopping for fresh produce directly from us. Browse our wide selection of quality fruits, vegetables, and organic produce.</p>
                    </div>
                    
                    <div class="cta-buttons">
                        <a href="{context['shop_url']}" class="btn btn-primary" style="display: inline-block; text-decoration: none;">🛒 Shop with Us</a>
                    </div>
                    
                    <p style="text-align: center; margin-top: 20px; font-size: 14px; color: #666;">
                        💡 Not interested right now? Simply close this email to exit.
                    </p>
                </div>
                <div class="footer">
                    <p>© 2026 Ankore Fresh Ltd. All rights reserved.</p>
                    <p><a href="{settings.SITE_URL}">Visit our website</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text alternative
        text_content = f"""
Welcome to Ankore Fresh, {context['user_name']}!

Thank you for registering with Ankore Fresh! Your account has been created successfully.

Account Type: {context['user_type']}

You can now start shopping for fresh produce directly from us. Browse our wide selection of quality fruits, vegetables, and organic produce.

Shop with Us: {context['shop_url']}

Contact Support: support@ankorefresh.com

© 2026 Ankore Fresh Ltd. All rights reserved.
        """
        
        # Create email
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        
        # Attach HTML version
        msg.attach_alternative(html_content, "text/html")
        
        # Send email
        msg.send(fail_silently=True)
        print(f"✅ Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send welcome email to {user.email}: {e}")
        return False
