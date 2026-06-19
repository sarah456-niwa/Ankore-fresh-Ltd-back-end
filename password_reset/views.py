from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import PasswordResetToken
from .serializers import ForgotPasswordSerializer, VerifyResetCodeSerializer, ResetPasswordSerializer

User = get_user_model()

class ForgotPasswordView(APIView):
    permission_classes = []
    
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'success': True,
                    'message': 'If an account exists with this email, a verification code has been sent.'
                }, status=status.HTTP_200_OK)
            
            PasswordResetToken.objects.filter(email=email, is_used=False).delete()
            token = PasswordResetToken.objects.create(user=user, email=email)
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 500px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h2>🔐 Password Reset</h2>
                    </div>
                    <div style="padding: 20px; background-color: #f9f9f9; border-radius: 0 0 10px 10px;">
                        <p>Hello {user.get_full_name() or user.username},</p>
                        <p>We received a request to reset your password. Use the verification code below:</p>
                        <div style="font-size: 32px; font-weight: bold; text-align: center; padding: 15px; background-color: #fff; border-radius: 8px; letter-spacing: 5px;">
                            {token.token}
                        </div>
                        <p>This code expires in 15 minutes.</p>
                        <p>If you didn't request this, please ignore this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            send_mail(
                subject='Password Reset Code - Ankore Fresh',
                message=f'Your password reset code is: {token.token}\n\nThis code expires in 15 minutes.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
                html_message=html_message
            )
            
            return Response({
                'success': True,
                'message': 'Verification code sent to your email'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyResetCodeView(APIView):
    permission_classes = []
    
    def post(self, request):
        serializer = VerifyResetCodeSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            
            try:
                token = PasswordResetToken.objects.get(email=email, token=code, is_used=False)
                if token.is_valid():
                    return Response({
                        'success': True,
                        'message': 'Code verified successfully',
                        'email': email
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': 'Code has expired. Please request a new one.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Invalid verification code'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = []
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']
            
            try:
                token = PasswordResetToken.objects.get(email=email, token=code, is_used=False)
                if token.is_valid():
                    user = token.user
                    user.set_password(new_password)
                    user.save()
                    
                    token.is_used = True
                    token.save()
                    
                    send_mail(
                        subject='Password Changed Successfully - Ankore Fresh',
                        message='Your password has been changed successfully.',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Password reset successfully'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': 'Code has expired. Please request a new one.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Invalid verification code'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)