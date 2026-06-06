from django.urls import path
from . import views

urlpatterns = [
    # Order Management
    path('', views.OrderListView.as_view(), name='order-list'),
    path('create/', views.OrderCreateView.as_view(), name='order-create'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/cancel/', views.OrderCancelView.as_view(), name='order-cancel'),
    path('<int:order_id>/status/', views.OrderStatusUpdateView.as_view(), name='order-status'),
    path('<int:order_id>/track/', views.OrderTrackingStatusView.as_view(), name='order-track-status'),
    path('track/<str:order_number>/', views.OrderTrackingView.as_view(), name='order-track'),
    
    # USER NOTIFICATION ENDPOINTS (for Flutter app)
    path('notifications/', views.UserNotificationsView.as_view(), name='user-notifications'),
    path('notifications/unread/count/', views.UnreadNotificationCountView.as_view(), name='unread-count'),
    path('notifications/<int:notification_id>/read/', views.UserMarkNotificationReadView.as_view(), name='mark-notification-read'),
    
    # ADMIN NOTIFICATION ENDPOINTS (for Django admin)
    path('admin/notifications/', views.AdminOrderNotificationsView.as_view(), name='admin-notifications'),
    path('admin/notifications/count/', views.GetUnreadNotificationCountView.as_view(), name='admin-notifications-count'),
    path('admin/notifications/<int:notification_id>/read/', views.AdminMarkNotificationReadView.as_view(), name='admin-mark-notification-read'),
    path('admin/notifications/read-all/', views.MarkAllNotificationsReadView.as_view(), name='mark-all-read'),
]