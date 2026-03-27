from django.urls import path
from . import views

urlpatterns = [
    # List and detail
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    
    # Actions
    path('mark-read/', views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('<int:notification_id>/mark-unread/', views.NotificationMarkUnreadView.as_view(), name='notification-mark-unread'),
    path('<int:notification_id>/delete/', views.NotificationDeleteView.as_view(), name='notification-delete'),
    path('clear-all/', views.NotificationClearAllView.as_view(), name='notification-clear-all'),
]