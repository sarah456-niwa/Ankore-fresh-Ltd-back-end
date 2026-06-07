from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/orders/track/(?P<order_number>[\w-]+)/$',
        consumers.OrderTrackingConsumer.as_asgi(),
        name='order_tracking_ws'
    ),
    re_path(
        r'ws/admin/notifications/$',
        consumers.AdminNotificationConsumer.as_asgi(),
        name='admin_notifications_ws'
    ),
    re_path(
        r'ws/notifications/user/$',
        consumers.UserNotificationConsumer.as_asgi(),
        name='user_notifications_ws'
    ),
]
