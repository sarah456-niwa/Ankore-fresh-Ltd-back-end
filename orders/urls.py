from django.urls import path
from . import views

urlpatterns = [
    # Order Management
    path('', views.OrderListView.as_view(), name='order-list'),
    path('create/', views.OrderCreateView.as_view(), name='order-create'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/cancel/', views.OrderCancelView.as_view(), name='order-cancel'),
    path('<int:order_id>/rate/', views.OrderRatingView.as_view(), name='order-rate'),
    
    # Status & Tracking
    path('<int:order_id>/status/', views.OrderStatusUpdateView.as_view(), name='order-status'),
    path('track/<str:order_number>/', views.OrderTrackingView.as_view(), name='order-track'),
    
    # Delivery
    path('<int:order_id>/assign-delivery/', views.DeliveryAssignmentView.as_view(), name='assign-delivery'),
    path('update-location/', views.DeliveryLocationUpdateView.as_view(), name='update-location'),
]