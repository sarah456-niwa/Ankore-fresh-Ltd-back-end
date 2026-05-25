from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from decimal import Decimal
from cart.models import Cart, CartItem
from .models import Order, OrderItem, OrderTracking, OrderNotification
from .serializers import OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer, OrderNotificationSerializer
from notifications.models import Notification


class OrderListView(generics.ListAPIView):
    """List user orders"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.user_type == 'admin':
            return Order.objects.all()
        return Order.objects.filter(user=user)


class OrderDetailView(generics.RetrieveAPIView):
    """Get order details"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.user_type == 'admin':
            return Order.objects.all()
        return Order.objects.filter(user=user)


@method_decorator(csrf_exempt, name='dispatch')
class OrderCreateView(generics.CreateAPIView):
    """Create new order from cart"""
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.AllowAny]
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        print("=" * 60)
        print("📦 RECEIVED ORDER REQUEST")
        print("=" * 60)
        
        data = request.data
        
        # Get or create user using your custom User model
        from users.models import User
        
        customer_name = data.get('customer_name') or data.get('name') or 'Customer'
        customer_email = data.get('customer_email') or data.get('email')
        customer_phone = data.get('customer_phone') or data.get('phone')
        
        user = None
        if customer_email:
            try:
                user = User.objects.get(email=customer_email)
                print(f"✅ Found existing user: {customer_email}")
            except User.DoesNotExist:
                username = customer_email.split('@')[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=customer_email,
                    password=username + '123',
                    user_type='immediate'
                )
                name_parts = customer_name.split(' ', 1)
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
                user.save()
                print(f"✅ Created new user: {customer_email}")
        
        if not user:
            temp_username = f"customer_{int(timezone.now().timestamp())}"
            user = User.objects.create_user(
                username=temp_username,
                email=f"{temp_username}@temp.com",
                password='temp123',
                user_type='immediate'
            )
            print(f"✅ Created temporary user: {temp_username}")
        
        request.user = user
        
        # Get or create cart
        cart, _ = Cart.objects.get_or_create(user=user)
        cart.items.all().delete()
        
        # Add items from request to cart
        items_data = data.get('items', [])
        
        if not items_data:
            product_id = data.get('product_id') or data.get('product')
            if product_id:
                items_data = [{'product_id': product_id, 'quantity': data.get('quantity', 1)}]
        
        if items_data:
            from products.models import Product
            for item_data in items_data:
                product_id = item_data.get('product_id') or item_data.get('product')
                quantity = item_data.get('quantity', 1)
                
                # Handle variant IDs (format: "2_standard" where 2 is the product ID)
                try:
                    # Check if product_id contains underscore (variant format)
                    if product_id and '_' in str(product_id):
                        # Extract the actual product ID (everything before the first underscore)
                        actual_product_id = int(str(product_id).split('_')[0])
                        product = Product.objects.get(id=actual_product_id)
                        print(f"✅ Found product from variant ID: {actual_product_id} (original: {product_id})")
                    else:
                        product = Product.objects.get(id=int(product_id))
                    
                    CartItem.objects.create(
                        cart=cart,
                        product=product,
                        quantity=quantity,
                        price_at_add=product.price
                    )
                    print(f"✅ Added to cart: {quantity} x {product.name}")
                except (Product.DoesNotExist, ValueError) as e:
                    print(f"⚠️ Product not found: {product_id}, Error: {e}")
                    return Response({
                        'success': False,
                        'error': f'Product not found: {product_id}'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        if cart.items.count() == 0:
            return Response({
                'success': False,
                'error': 'No items provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract delivery details
        delivery_address = data.get('delivery_address') or data.get('address') or ''
        delivery_phone = data.get('delivery_phone') or data.get('phone') or customer_phone or ''
        delivery_instructions = data.get('delivery_instructions') or data.get('instructions') or ''
        payment_method = data.get('payment_method') or data.get('paymentMethod') or 'cash'
        payment_method = payment_method.lower()
        if payment_method not in ['cash', 'momo', 'airtel', 'card']:
            payment_method = 'cash'
        notes = data.get('notes') or ''
        
        print(f"📝 Customer: {customer_name}")
        print(f"📝 Customer Email: {customer_email}")
        print(f"📝 Customer Phone: {customer_phone}")
        print(f"📝 Delivery: {delivery_address}")
        print(f"📝 Payment: {payment_method}")
        
        # Calculate totals
        subtotal = cart.total_amount
        delivery_fee = Decimal('5000')
        service_fee = (subtotal * Decimal('0.02')).quantize(Decimal('1'))
        tax = (subtotal * Decimal('0.05')).quantize(Decimal('1'))
        total = subtotal + delivery_fee + service_fee + tax
        
        # Create order
        order = Order.objects.create(
            user=user,
            customer_name=customer_name,
            customer_email=customer_email or user.email,
            customer_phone=customer_phone,
            delivery_address=delivery_address,
            delivery_phone=delivery_phone,
            delivery_instructions=delivery_instructions,
            payment_method=payment_method,
            notes=notes,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            service_fee=service_fee,
            tax=tax,
            total=total
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                seller=cart_item.product.seller,
                product_name=cart_item.product.name,
                product_image=cart_item.product.image.url if cart_item.product.image else '',
                price=cart_item.price_at_add,
                quantity=cart_item.quantity
            )
            cart_item.product.stock -= cart_item.quantity
            cart_item.product.save()
            print(f"   ✅ Added: {cart_item.quantity} x {cart_item.product.name}")
        
        # Clear cart
        cart.items.all().delete()
        
        # Create tracking entry
        OrderTracking.objects.create(
            order=order,
            status=order.status,
            notes="Order created successfully"
        )
        
        # Create admin notification
        OrderNotification.objects.create(order=order)
        
        # Send notifications
        self.send_order_confirmation_email(order)
        self.send_sms_notification(order)
        self.send_admin_notification(order)
        
        # Create in-app notification for user
        Notification.objects.create(
            user=user,
            title="Order Confirmed",
            message=f"Your order #{order.order_number} has been received",
            notification_type='order',
            data={'order_id': order.id, 'order_number': order.order_number}
        )
        
        print(f"✅ ORDER COMPLETE: {order.order_number}")
        print("=" * 60)
        
        return Response({
            'success': True,
            'order_number': order.order_number,
            'id': order.id,
            'message': 'Order placed successfully'
        }, status=status.HTTP_201_CREATED)
    
    def send_order_confirmation_email(self, order):
        if not order.customer_email:
            print(f"⚠️ No email for order {order.order_number}")
            return
        
        subject = f"Order Confirmation - {order.order_number}"
        html_message = f"""
        <html>
        <body>
            <h2>Thank You for Your Order!</h2>
            <p>Dear {order.customer_name or 'Customer'},</p>
            <p>Your order #{order.order_number} has been received.</p>
            <h3>Order Details:</h3>
            <p><strong>Order Date:</strong> {order.created_at.strftime('%Y-%m-%d %H:%M')}</p>
            <p><strong>Payment Method:</strong> {order.get_payment_method_display()}</p>
            <p><strong>Delivery Address:</strong> {order.delivery_address}</p>
            <h4>Items:</h4>
            <ul>
        """
        for item in order.items.all():
            html_message += f"<li>{item.quantity} x {item.product_name} - UGX {item.price:,.0f}</li>"
        
        html_message += f"""
            </ul>
            <p><strong>Total:</strong> UGX {order.total:,.0f}</p>
            <p>We'll notify you when your order is ready.</p>
            <p>Thank you for shopping with Ankore Fresh!</p>
        </body>
        </html>
        """
        
        send_mail(
            subject=subject,
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer_email],
            fail_silently=False,
            html_message=html_message
        )
        print(f"📧 Email sent to {order.customer_email}")
    
    def send_sms_notification(self, order):
        if not order.customer_phone:
            print(f"⚠️ No phone for order {order.order_number}")
            return
        print(f"📱 SMS to {order.customer_phone}: Order #{order.order_number} confirmed. Total: UGX {order.total:,.0f}")
    
    def send_admin_notification(self, order):
        from users.models import User
        admin_emails = list(User.objects.filter(is_superuser=True).values_list('email', flat=True))
        
        subject = f"🛍️ NEW ORDER - {order.order_number}"
        html_message = f"""
        <html>
        <body>
            <h2>New Order!</h2>
            <p><strong>Order:</strong> {order.order_number}</p>
            <p><strong>Customer:</strong> {order.customer_name}</p>
            <p><strong>Email:</strong> {order.customer_email}</p>
            <p><strong>Phone:</strong> {order.customer_phone}</p>
            <p><strong>Delivery:</strong> {order.delivery_address}</p>
            <p><strong>Payment:</strong> {order.get_payment_method_display()}</p>
            <p><strong>Total:</strong> UGX {order.total:,.0f}</p>
            <h4>Items:</h4>
            <ul>
        """
        for item in order.items.all():
            html_message += f"<li>{item.quantity} x {item.product_name} - UGX {item.price:,.0f}</li>"
        
        html_message += f"""
            </ul>
            <p><a href="{settings.SITE_URL}/admin/orders/order/{order.id}/change/">View Order in Admin</a></p>
        </body>
        </html>
        """
        
        for email in admin_emails:
            if email:
                send_mail(
                    subject=subject,
                    message="",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                    html_message=html_message
                )
        print(f"📧 Admin notification sent")


class OrderTrackingStatusView(APIView):
    """Get tracking information"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        tracking_history = []
        for tracking in order.tracking_history.all():
            tracking_history.append({
                'status': tracking.status,
                'status_display': tracking.get_status_display(),
                'location': tracking.location,
                'notes': tracking.notes,
                'timestamp': tracking.created_at.isoformat(),
            })
        
        return Response({
            'order_number': order.order_number,
            'status': order.status,
            'status_display': order.get_status_display(),
            'estimated_delivery': order.estimated_delivery,
            'current_location': order.current_location,
            'delivery_address': order.delivery_address,
            'delivery_phone': str(order.delivery_phone),
            'tracking_history': tracking_history,
        })


@method_decorator(csrf_exempt, name='dispatch')
class OrderCancelView(APIView):
    """Cancel order"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not order.can_cancel:
            return Response({'error': 'Order cannot be cancelled'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'cancelled'
        order.save()
        
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()
        
        OrderTracking.objects.create(
            order=order,
            status='cancelled',
            notes=request.data.get('reason', 'Cancelled by user')
        )
        
        return Response({'message': 'Order cancelled successfully'})


@method_decorator(csrf_exempt, name='dispatch')
class OrderStatusUpdateView(APIView):
    """Update order status and send notifications"""
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not (request.user.is_superuser or request.user.user_type in ['admin', 'delivery']):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = OrderStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            old_status = order.status
            new_status = serializer.validated_data['status']
            location = serializer.validated_data.get('location', '')
            notes = serializer.validated_data.get('notes', '')
            
            order.status = new_status
            order.current_location = location
            order.save()
            
            # Create tracking entry
            OrderTracking.objects.create(
                order=order,
                status=new_status,
                location=location,
                notes=notes
            )
            
            # Send notifications based on status change
            self._send_status_notifications(order, old_status, new_status, notes)
            
            # Create in-app notification for user
            Notification.objects.create(
                user=order.user,
                title=f"Order {new_status.replace('_', ' ').title()}",
                message=f"Your order #{order.order_number} status: {order.get_status_display()}\n{notes if notes else ''}",
                notification_type='delivery',
                data={'order_id': order.id, 'status': new_status}
            )
            
            return Response(OrderSerializer(order).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _send_status_notifications(self, order, old_status, new_status, notes):
        """Send email and SMS notifications for status updates"""
        
        # Email templates for different statuses
        email_templates = {
            'confirmed': {
                'subject': f'Order Confirmed - {order.order_number}',
                'message': f"""
Dear {order.customer_name or 'Customer'},

Your order #{order.order_number} has been confirmed!

Order Details:
- Order Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}
- Total Amount: UGX {order.total:,.0f}
- Payment Method: {order.get_payment_method_display()}
- Delivery Address: {order.delivery_address}

We'll notify you when your order is ready for delivery.

Thank you for shopping with Ankore Fresh!
"""
            },
            'processing': {
                'subject': f'Order Being Prepared - {order.order_number}',
                'message': f"""
Dear {order.customer_name or 'Customer'},

Great news! Your order #{order.order_number} is now being prepared.

Our team is carefully packaging your items.

Total: UGX {order.total:,.0f}

Thank you for shopping with Ankore Fresh!
"""
            },
            'shipped': {
                'subject': f'Order Shipped - {order.order_number}',
                'message': f"""
Dear {order.customer_name or 'Customer'},

Your order #{order.order_number} has been picked up by our delivery partner!

You can track your order in real-time using our app.

Thank you for shopping with Ankore Fresh!
"""
            },
            'out_for_delivery': {
                'subject': f'Order Out for Delivery - {order.order_number}',
                'message': f"""
Dear {order.customer_name or 'Customer'},

Your order #{order.order_number} is out for delivery!

Our delivery agent will arrive shortly.
Please ensure someone is available to receive the order.

Delivery Address: {order.delivery_address}

Track your delivery in real-time through the app.

Thank you for shopping with Ankore Fresh!
"""
            },
            'delivered': {
                'subject': f'Order Delivered - {order.order_number}',
                'message': f"""
Dear {order.customer_name or 'Customer'},

Your order #{order.order_number} has been delivered successfully!

We hope you enjoy your fresh produce!

Please rate your order in the app to help us improve.

Thank you for choosing Ankore Fresh!
"""
            },
            'cancelled': {
                'subject': f'Order Cancelled - {order.order_number}',
                'message': f"""
Dear {order.customer_name or 'Customer'},

Your order #{order.order_number} has been cancelled.

If you have any questions, please contact our support team.

Thank you for shopping with Ankore Fresh!
"""
            }
        }
        
        # Send email if template exists for this status
        if new_status in email_templates and order.customer_email:
            template = email_templates[new_status]
            try:
                send_mail(
                    subject=template['subject'],
                    message=template['message'],
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.customer_email],
                    fail_silently=False,
                )
                print(f"📧 Status update email sent to {order.customer_email} for status: {new_status}")
            except Exception as e:
                print(f"❌ Failed to send email: {e}")
        
        # Send SMS for critical statuses
        if new_status in ['out_for_delivery', 'delivered'] and order.customer_phone:
            self._send_sms_update(order, new_status)
    
    def _send_sms_update(self, order, status):
        sms_messages = {
            'out_for_delivery': f"Ankore Fresh: Your order #{order.order_number} is out for delivery! Track in app.",
            'delivered': f"Ankore Fresh: Your order #{order.order_number} has been delivered! Rate your experience in the app."
        }
        
        message = sms_messages.get(status, "")
        if message:
            print(f"📱 SMS to {order.customer_phone}: {message}")


class OrderTrackingView(APIView):
    """Track order by number"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        tracking = OrderTracking.objects.filter(order=order)
        
        return Response({
            'order_number': order.order_number,
            'status': order.status,
            'status_display': order.get_status_display(),
            'tracking_number': order.tracking_number,
            'estimated_delivery': order.estimated_delivery,
            'current_location': order.current_location,
            'delivery_address': order.delivery_address,
            'delivery_phone': str(order.delivery_phone),
            'customer_name': order.customer_name,
            'customer_email': order.customer_email,
            'customer_phone': order.customer_phone,
            'tracking_history': [
                {
                    'status': t.get_status_display(),
                    'location': t.location,
                    'notes': t.notes,
                    'timestamp': t.created_at
                }
                for t in tracking
            ]
        })


# ========== USER NOTIFICATION ENDPOINTS (for Flutter app) ==========

class UserNotificationsView(APIView):
    """Get user's order notifications"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Return empty if not authenticated
        if not request.user.is_authenticated:
            return Response({
                'notifications': [],
                'unread_count': 0
            })
        
        notifications = Notification.objects.filter(
            user=request.user,
            notification_type='delivery'
        ).order_by('-created_at')[:50]
        
        return Response({
            'notifications': [
                {
                    'id': n.id,
                    'title': n.title,
                    'message': n.message,
                    'is_read': n.is_read,
                    'created_at': n.created_at,
                    'data': n.data
                }
                for n in notifications
            ],
            'unread_count': notifications.filter(is_read=False).count()
        })


class UnreadNotificationCountView(APIView):
    """Get unread notification count"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Return 0 if not authenticated
        if not request.user.is_authenticated:
            return Response({'count': 0})
        
        count = Notification.objects.filter(
            user=request.user,
            notification_type='delivery',
            is_read=False
        ).count()
        return Response({'count': count})


@method_decorator(csrf_exempt, name='dispatch')
class MarkNotificationReadView(APIView):
    """Mark a notification as read"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({'success': True})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)


# ========== ADMIN NOTIFICATION ENDPOINTS (for Django admin) ==========

class AdminOrderNotificationsView(APIView):
    """Get unread order notifications for admin"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if not (request.user.is_superuser or request.user.user_type == 'admin'):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        notifications = OrderNotification.objects.filter(is_read=False).select_related('order')
        serializer = OrderNotificationSerializer(notifications, many=True)
        
        return Response({
            'count': notifications.count(),
            'notifications': serializer.data
        })


class GetUnreadNotificationCountView(APIView):
    """Get only the count of unread notifications for admin"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if not (request.user.is_superuser or request.user.user_type == 'admin'):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        count = OrderNotification.objects.filter(is_read=False).count()
        return Response({'count': count})


@method_decorator(csrf_exempt, name='dispatch')
class MarkNotificationReadView(APIView):
    """Mark a single notification as read (admin)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, notification_id):
        if not (request.user.is_superuser or request.user.user_type == 'admin'):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            notification = OrderNotification.objects.get(id=notification_id)
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            return Response({'success': True})
        except OrderNotification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name='dispatch')
class MarkAllNotificationsReadView(APIView):
    """Mark all notifications as read (admin)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if not (request.user.is_superuser or request.user.user_type == 'admin'):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        updated_count = OrderNotification.objects.filter(is_read=False).update(
            is_read=True, 
            read_at=timezone.now()
        )
        
        return Response({
            'success': True,
            'marked_count': updated_count
        })