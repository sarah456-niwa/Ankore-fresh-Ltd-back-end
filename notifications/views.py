from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        notification_ids = request.data.get('notification_ids', [])
        Notification.objects.filter(id__in=notification_ids, user=request.user).update(is_read=True)
        return Response({'message': 'Notifications marked as read'})

class NotificationDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.delete()
            return Response({'message': 'Notification deleted'})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)