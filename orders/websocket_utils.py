import asyncio
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


def send_order_update_websocket(order_number, order_data):
    """
    Send order update via WebSocket to all connected clients tracking this order
    
    Args:
        order_number (str): The order number to update
        order_data (dict): The serialized order data to send
    """
    try:
        channel_layer = get_channel_layer()
        group_name = f'order_{order_number}'
        
        # Send message to the group
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'order_update',
                'data': order_data,
            }
        )
        
        logger.info(f"✅ WebSocket update sent for order {order_number}")
        return True
    except Exception as e:
        logger.error(f"❌ Error sending WebSocket update for order {order_number}: {e}")
        return False


def send_admin_notification_websocket(order_id, notification_id, message, notification_type='order_update'):
    """
    Send admin notification via WebSocket to all connected admin clients
    
    Args:
        order_id (int): The order ID
        notification_id (int): The notification ID
        message (str): The notification message
        notification_type (str): Type of notification (order_cancelled, order_update, etc.)
    """
    try:
        channel_layer = get_channel_layer()
        group_name = 'admin_notifications'
        
        # Send message to admin group
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'admin_notification',
                'data': {
                    'order_id': order_id,
                    'notification_id': notification_id,
                    'message': message,
                    'notification_type': notification_type,
                    'timestamp': __import__('time').time()
                }
            }
        )
        
        logger.info(f"✅ Admin notification sent: {message}")
        return True
    except Exception as e:
        logger.error(f"❌ Error sending admin notification: {e}")
        return False
