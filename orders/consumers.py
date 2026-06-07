import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
import logging

logger = logging.getLogger(__name__)


class OrderTrackingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time order tracking updates"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Get the order number from URL kwargs
        self.order_number = self.scope['url_route']['kwargs'].get('order_number')
        self.user = self.scope['user']
        
        if not self.order_number:
            await self.close()
            return
        
        # Create a unique group name for this order
        self.room_group_name = f'order_{self.order_number}'
        
        # Log connection
        logger.info(f"✅ WebSocket connecting for order {self.order_number}")
        
        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"✅ WebSocket connected for order {self.order_number}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            logger.info(f"❌ WebSocket disconnecting for order {self.room_group_name}")
            
            # Leave the room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Simple ping/pong to keep connection alive
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': __import__('time').time()
                }))
            elif message_type == 'subscribe':
                # Client confirming subscription
                order_data = await self.get_order_data()
                if order_data:
                    await self.send(text_data=json.dumps({
                        'type': 'order_update',
                        'data': order_data
                    }))
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received on order {self.order_number}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    async def order_update(self, event):
        """Handle order update message from group"""
        # Send the order update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_order_data(self):
        """Fetch current order data from database"""
        from .models import Order
        from .serializers import OrderSerializer
        
        try:
            order = Order.objects.get(order_number=self.order_number)
            
            # Check if user has permission to access this order
            if self.user.is_authenticated:
                if not (self.user == order.user or self.user.is_superuser or self.user.user_type == 'admin'):
                    return None
            
            serializer = OrderSerializer(order)
            return serializer.data
        except Order.DoesNotExist:
            return None


class AdminNotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for admin notifications"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope['user']
        
        # Only allow authenticated admins
        if not self.user.is_authenticated:
            await self.close()
            return
        
        if not (self.user.is_superuser or self.user.user_type == 'admin'):
            await self.close()
            return
        
        # Add to admin notifications group
        self.group_name = 'admin_notifications'
        
        logger.info(f"✅ Admin {self.user.email} connected for notifications")
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'group_name'):
            logger.info(f"❌ Admin disconnecting from notifications")
            
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': __import__('time').time()
                }))
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received by admin")
        except Exception as e:
            logger.error(f"Error processing admin WebSocket message: {e}")
    
    async def admin_notification(self, event):
        """Handle admin notification message from group"""
        # Send the notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data']
        }))


class UserNotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for per-user notifications (red-dot badge etc.)"""

    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f'user_{self.user.id}_notifications'

        logger.info(f"✅ User {self.user.email} connected for notifications")

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            logger.info(f"❌ User disconnecting from notifications")
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong', 'timestamp': __import__('time').time()}))
        except json.JSONDecodeError:
            logger.error('Invalid JSON received by user notification consumer')
        except Exception as e:
            logger.error(f'Error in user notification receive: {e}')

    async def user_notification(self, event):
        await self.send(text_data=json.dumps({'type': 'notification', 'data': event['data']}))
