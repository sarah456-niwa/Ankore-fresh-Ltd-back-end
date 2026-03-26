from django.contrib import admin
from django.utils.html import format_html
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'user', 
        'title', 
        'notification_type', 
        'is_read', 
        'created_at',
        'preview_message'
    ]
    list_filter = [
        'notification_type', 
        'is_read', 
        'created_at',
        'user__user_type'
    ]
    search_fields = [
        'title', 
        'message', 
        'user__email', 
        'user__username'
    ]
    readonly_fields = ['created_at', 'data_preview']
    
    fieldsets = (
        ('Notification Information', {
            'fields': (
                'user', 
                'title', 
                'message', 
                'notification_type'
            )
        }),
        ('Status', {
            'fields': (
                'is_read',
                'created_at'
            )
        }),
        ('Additional Data', {
            'fields': ('data', 'data_preview'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'delete_selected']
    
    def preview_message(self, obj):
        """Display a preview of the message"""
        if len(obj.message) > 50:
            return f"{obj.message[:50]}..."
        return obj.message
    preview_message.short_description = 'Message Preview'
    
    def data_preview(self, obj):
        """Display a readable preview of JSON data"""
        if obj.data:
            import json
            return format_html(
                '<pre style="background:#f5f5f5; padding:10px; border-radius:5px;">{}</pre>',
                json.dumps(obj.data, indent=2)
            )
        return "No additional data"
    data_preview.short_description = 'Data Preview'
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = "Mark selected as unread"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')
    
    def get_readonly_fields(self, request, obj=None):
        """Make fields read-only for non-superusers"""
        if not request.user.is_superuser:
            return self.readonly_fields + ['user', 'notification_type']
        return self.readonly_fields
    
    def has_delete_permission(self, request, obj=None):
        """Allow delete only for superusers"""
        if request.user.is_superuser:
            return True
        return False
    
    class Media:
        css = {
            'all': ('admin/css/notification_admin.css',)
        }
        js = ('admin/js/notification_admin.js',)