# ankore/admin.py
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum
from django.contrib.auth import get_user_model

# Import the custom UserAdmin
from users.admin import CustomUserAdmin
from users.models import User
from products.models import Category, Product
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem, OrderTracking
from notifications.models import Notification

User = get_user_model()

class AnkoreAdminSite(AdminSite):
    site_header = 'Ankore Fresh Admin'
    site_title = 'Ankore Fresh Admin Portal'
    index_title = 'Dashboard'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        from products.models import Product, Category
        from orders.models import Order, OrderItem
        
        # Get current date and 30 days ago
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # User Statistics
        total_users = User.objects.count()
        total_sellers = User.objects.filter(user_type='bulk').count()
        verified_sellers = User.objects.filter(user_type='bulk', is_verified_seller=True).count()
        pending_sellers = total_sellers - verified_sellers
        total_delivery_agents = User.objects.filter(user_type='delivery').count()
        available_delivery = User.objects.filter(user_type='delivery', is_available=True).count()
        
        # Product Statistics
        total_products = Product.objects.filter(is_active=True).count()
        low_stock_products = Product.objects.filter(stock__lt=10, is_active=True).count()
        out_of_stock_products = Product.objects.filter(stock=0, is_active=True).count()
        total_categories = Category.objects.count()
        
        # Order Statistics
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        processing_orders = Order.objects.filter(status__in=['confirmed', 'processing']).count()
        delivered_orders = Order.objects.filter(status='delivered').count()
        cancelled_orders = Order.objects.filter(status='cancelled').count()
        
        # Revenue Statistics
        revenue_result = Order.objects.filter(status='delivered', payment_status='paid').aggregate(
            total=Sum('total')
        )
        total_revenue = revenue_result['total'] or 0
        
        # Recent Orders
        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
        
        # Recent Users
        recent_users = User.objects.order_by('-date_joined')[:10]
        
        # Top Selling Products
        top_products = OrderItem.objects.values('product_name').annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold')[:5]
        
        context = {
            'title': 'Dashboard',
            'total_users': total_users,
            'total_sellers': total_sellers,
            'verified_sellers': verified_sellers,
            'pending_sellers': pending_sellers,
            'total_delivery_agents': total_delivery_agents,
            'available_delivery': available_delivery,
            'total_products': total_products,
            'low_stock_products': low_stock_products,
            'out_of_stock_products': out_of_stock_products,
            'total_categories': total_categories,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
            'delivered_orders': delivered_orders,
            'cancelled_orders': cancelled_orders,
            'total_revenue': total_revenue,
            'recent_orders': recent_orders,
            'recent_users': recent_users,
            'top_products': top_products,
        }
        return TemplateResponse(request, 'admin/dashboard.html', context)

# Create the custom admin site
admin_site = AnkoreAdminSite(name='ankore_admin')

# Register all models with the custom admin site
admin_site.register(User, CustomUserAdmin)
admin_site.register(Category)
admin_site.register(Product)
admin_site.register(Cart)
admin_site.register(CartItem)
admin_site.register(Order)
admin_site.register(OrderItem)
admin_site.register(OrderTracking)
admin_site.register(Notification)