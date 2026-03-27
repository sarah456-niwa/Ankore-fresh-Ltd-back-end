from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Notification
from .serializers import NotificationSerializer, NotificationMarkReadSerializer

class NotificationListView(generics.ListAPIView):
    """List all notifications for the authenticated user"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Optional: filter by read/unread
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)
        
        return queryset

class NotificationDetailView(generics.RetrieveAPIView):
    """Get a single notification"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class NotificationMarkReadView(APIView):
    """Mark notifications as read"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = NotificationMarkReadSerializer(data=request.data)
        if serializer.is_valid():
            mark_all = serializer.validated_data.get('mark_all', False)
            notification_ids = serializer.validated_data.get('notification_ids', [])
            
            if mark_all:
                # Mark all notifications as read
                Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
                return Response({'message': 'All notifications marked as read'})
            elif notification_ids:
                # Mark specific notifications as read
                updated = Notification.objects.filter(
                    id__in=notification_ids, 
                    user=request.user
                ).update(is_read=True)
                return Response({'message': f'{updated} notifications marked as read'})
            else:
                return Response(
                    {'error': 'Either mark_all=true or notification_ids must be provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationMarkUnreadView(APIView):
    """Mark notification as unread"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = False
        notification.save()
        return Response({'message': 'Notification marked as unread'})

class NotificationDeleteView(APIView):
    """Delete a notification"""
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.delete()
        return Response({'message': 'Notification deleted'}, status=status.HTTP_204_NO_CONTENT)

class NotificationClearAllView(APIView):
    """Delete all notifications for the user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request):
        count = Notification.objects.filter(user=request.user).delete()[0]
        return Response({'message': f'{count} notifications cleared'})