from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from cart.models import Cart
from .models import Order, OrderItem, OrderTracking
from .serializers import OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer
from notifications.models import Notification
from payments.utils import process_payment

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

class OrderCreateView(generics.CreateAPIView):
    """Create new order from cart"""
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        
        # Get cart items
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            raise serializers.ValidationError({"cart": "Cart is empty"})
        
        if cart.items.count() == 0:
            raise serializers.ValidationError({"cart": "Cart is empty"})
        
        # Calculate order totals
        subtotal = cart.total_amount
        delivery_fee = self.calculate_delivery_fee(serializer.validated_data.get('delivery_address', ''))
        service_fee = int(subtotal * 0.02)  # 2% service fee
        discount = 0
        tax = int(subtotal * 0.05)  # 5% tax
        
        total = subtotal + delivery_fee + service_fee - discount + tax
        
        # Create order
        order = Order.objects.create(
            user=user,
            delivery_address=serializer.validated_data['delivery_address'],
            delivery_phone=serializer.validated_data['delivery_phone'],
            delivery_instructions=serializer.validated_data.get('delivery_instructions', ''),
            delivery_date=serializer.validated_data.get('delivery_date'),
            delivery_time_slot=serializer.validated_data.get('delivery_time_slot', ''),
            payment_method=serializer.validated_data['payment_method'],
            notes=serializer.validated_data.get('notes', ''),
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            service_fee=service_fee,
            discount=discount,
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
            
            # Update product stock
            cart_item.product.stock -= cart_item.quantity
            cart_item.product.save()
        
        # Clear cart
        cart.items.all().delete()
        
        # Process payment if not cash on delivery
        payment_status = 'pending'
        if order.payment_method != 'cash':
            try:
                payment_result = process_payment(order, serializer.validated_data['payment_method'])
                if payment_result.get('success'):
                    payment_status = 'paid'
                    order.payment_status = 'paid'
                    order.status = 'confirmed'
                else:
                    payment_status = 'failed'
            except Exception as e:
                payment_status = 'failed'
        
        order.payment_status = payment_status
        if payment_status == 'paid':
            order.status = 'confirmed'
        order.save()
        
        # Create tracking entry
        OrderTracking.objects.create(
            order=order,
            status=order.status,
            notes="Order created successfully"
        )
        
        # Create notifications
        Notification.objects.create(
            user=user,
            title="Order Placed",
            message=f"Your order #{order.order_number} has been placed successfully",
            notification_type='order',
            data={'order_id': order.id, 'order_number': order.order_number}
        )
        
        # Notify admin for seller orders
        for item in order.items.all():
            if item.seller:
                Notification.objects.create(
                    user=item.seller,
                    title="New Order Received",
                    message=f"New order #{order.order_number} for {item.product_name}",
                    notification_type='order',
                    data={'order_id': order.id, 'product_id': item.product.id}
                )
        
        return order
    
    def calculate_delivery_fee(self, address):
        """Calculate delivery fee based on distance"""
        # Simplified delivery fee calculation
        # In production, integrate with Google Maps API
        return 5000  # Base delivery fee UGX

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
        
        # Restore product stock
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()
        
        # Create tracking entry
        OrderTracking.objects.create(
            order=order,
            status='cancelled',
            notes=request.data.get('reason', 'Cancelled by user')
        )
        
        # Create notification
        Notification.objects.create(
            user=request.user,
            title="Order Cancelled",
            message=f"Your order #{order.order_number} has been cancelled",
            notification_type='order',
            data={'order_id': order.id}
        )
        
        return Response({'message': 'Order cancelled successfully'})

class OrderStatusUpdateView(APIView):
    """Update order status (Admin/Delivery only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions
        if not (request.user.is_superuser or request.user.user_type in ['admin', 'delivery']):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = OrderStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            old_status = order.status
            new_status = serializer.validated_data['status']
            
            order.status = new_status
            order.save()
            
            # Create tracking entry
            OrderTracking.objects.create(
                order=order,
                status=new_status,
                location=serializer.validated_data.get('location', ''),
                notes=serializer.validated_data.get('notes', '')
            )
            
            # Notify user
            Notification.objects.create(
                user=order.user,
                title=f"Order {new_status.replace('_', ' ').title()}",
                message=f"Your order #{order.order_number} status updated to {order.get_status_display()}",
                notification_type='delivery',
                data={'order_id': order.id, 'status': new_status}
            )
            
            return Response(OrderSerializer(order).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderTrackingView(APIView):
    """Track order status"""
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

class OrderRatingView(APIView):
    """Rate and review order"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if order.status != 'delivered':
            return Response({'error': 'Can only rate delivered orders'}, status=status.HTTP_400_BAD_REQUEST)
        
        rating = request.data.get('rating')
        feedback = request.data.get('feedback', '')
        
        if rating and 1 <= int(rating) <= 5:
            order.customer_rating = rating
            order.customer_feedback = feedback
            order.save()
            
            return Response({'message': 'Rating submitted successfully'})
        
        return Response({'error': 'Invalid rating'}, status=status.HTTP_400_BAD_REQUEST)

class DeliveryAssignmentView(APIView):
    """Assign delivery agent to order"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, order_id):
        if not (request.user.is_superuser or request.user.user_type == 'admin'):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        agent_id = request.data.get('delivery_agent_id')
        
        from users.models import User
        try:
            agent = User.objects.get(id=agent_id, user_type='delivery')
        except User.DoesNotExist:
            return Response({'error': 'Delivery agent not found'}, status=status.HTTP_404_NOT_FOUND)
        
        order.delivery_agent = agent
        order.status = 'processing'
        order.save()
        
        # Notify delivery agent
        Notification.objects.create(
            user=agent,
            title="New Delivery Assignment",
            message=f"You have been assigned to deliver order #{order.order_number}",
            notification_type='delivery',
            data={'order_id': order.id}
        )
        
        # Notify customer
        Notification.objects.create(
            user=order.user,
            title="Delivery Agent Assigned",
            message=f"A delivery agent has been assigned to your order #{order.order_number}",
            notification_type='delivery',
            data={'order_id': order.id}
        )
        
        return Response(OrderSerializer(order).data)

class DeliveryLocationUpdateView(APIView):
    """Update delivery location in real-time"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if request.user.user_type != 'delivery':
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        order_id = request.data.get('order_id')
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        location = request.data.get('location')
        
        try:
            order = Order.objects.get(id=order_id, delivery_agent=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if lat and lng:
            order.location_lat = lat
            order.location_lng = lng
        
        if location:
            order.current_location = location
        
        order.save()
        
        return Response({'message': 'Location updated'})