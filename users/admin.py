from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User

class CustomUserAdmin(UserAdmin):
    # Display fields in the list view
    list_display = [
        'id', 
        'email', 
        'username', 
        'get_full_name', 
        'phone', 
        'user_type', 
        'is_verified_seller',
        'is_available',
        'is_active', 
        'date_joined',
        'profile_picture_preview'
    ]
    
    # Filters for the sidebar
    list_filter = [
        'user_type', 
        'is_verified_seller', 
        'is_available',
        'is_active', 
        'is_staff', 
        'is_superuser',
        'date_joined'
    ]
    
    # Search fields
    search_fields = [
        'email', 
        'username', 
        'first_name', 
        'last_name', 
        'phone', 
        'store_name',
        'business_address'
    ]
    
    # Fields that can be edited directly in the list view
    list_editable = ['user_type', 'is_verified_seller', 'is_available', 'is_active']
    
    # Order by
    ordering = ('-date_joined',)
    
    # Fields to display in the detail/edit form
    fieldsets = (
        ('Login Information', {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal Information', {
            'fields': (
                ('first_name', 'last_name'),
                'phone',
                'profile_picture',
                'profile_picture_preview',
                'location',
                'date_of_birth'
            )
        }),
        ('Account Type', {
            'fields': ('user_type', 'is_verified_seller'),
            'description': 'User type determines what features are available'
        }),
        ('Business Information (for Bulk Sellers)', {
            'fields': ('store_name', 'business_address', 'tax_id'),
            'classes': ('collapse',),
            'description': 'Required for bulk sellers to start selling'
        }),
        ('Delivery Agent Information', {
            'fields': ('current_lat', 'current_lng', 'is_available'),
            'classes': ('collapse',),
            'description': 'Location tracking for delivery agents'
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Fields for creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'user_type', 'password1', 'password2'),
        }),
    )
    
    # Read-only fields
    readonly_fields = [
        'date_joined', 
        'updated_at', 
        'last_login',
        'profile_picture_preview'
    ]
    
    # Custom methods for display
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'
    
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                obj.profile_picture.url
            )
        return format_html(
            '<div style="width: 50px; height: 50px; background: #e0e0e0; border-radius: 50%; display: flex; align-items: center; justify-content: center;">'
            '<span style="font-size: 20px;">👤</span></div>'
        )
    profile_picture_preview.short_description = 'Profile Picture'
    
    # Bulk actions
    actions = ['verify_sellers', 'make_available', 'make_unavailable']
    
    def verify_sellers(self, request, queryset):
        updated = queryset.filter(user_type='bulk').update(is_verified_seller=True)
        self.message_user(request, f'{updated} seller(s) verified successfully.')
    verify_sellers.short_description = "Verify selected sellers"
    
    def make_available(self, request, queryset):
        updated = queryset.filter(user_type='delivery').update(is_available=True)
        self.message_user(request, f'{updated} delivery agent(s) marked as available.')
    make_available.short_description = "Mark delivery agents as available"
    
    def make_unavailable(self, request, queryset):
        updated = queryset.filter(user_type='delivery').update(is_available=False)
        self.message_user(request, f'{updated} delivery agent(s) marked as unavailable.')
    make_unavailable.short_description = "Mark delivery agents as unavailable"
    
    # Save method to ensure username is set from email if not provided
    def save_model(self, request, obj, form, change):
        if not obj.username:
            obj.username = obj.email.split('@')[0]
        super().save_model(request, obj, form, change)

# Register the custom user admin
admin.site.register(User, CustomUserAdmin)