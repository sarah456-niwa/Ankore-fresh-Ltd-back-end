from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserDetailSerializer
from .models import User
from .models import PasswordResetCode
from .utils import send_sms
from django.utils import timezone
from datetime import timedelta
import random

class RegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserDetailSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        # Log serializer errors and the incoming payload to aid debugging of bad requests
        try:
            print(f"❌ Registration validation errors: {serializer.errors}")
            try:
                print(f"📥 Registration payload: {request.data}")
            except Exception:
                pass
        except Exception:
            pass
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserDetailSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({'message': 'Logout successful'})
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ========== NEW: Mobile Session Login View ==========
@method_decorator(csrf_exempt, name='dispatch')
class MobileLoginView(APIView):
    """
    Mobile login view that uses Django session authentication.
    This creates a session cookie that will be used for subsequent requests.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'success': False,
                'message': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Authenticate user
        user = authenticate(request, username=user.username, password=password)
        
        if user is not None:
            # Login the user - this creates the session
            login(request, user)
            
            # Also generate JWT tokens for mobile app
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.get_full_name() or user.username,
                    'phone': getattr(user, 'phone', ''),
                    'user_type': getattr(user, 'user_type', 'immediate'),
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)

# ========== Optional: Check Session Status View ==========
class SessionStatusView(APIView):
    """
    Check if user is authenticated via session
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'is_authenticated': True,
                'user': {
                    'id': request.user.id,
                    'email': request.user.email,
                    'full_name': request.user.get_full_name() or request.user.username,
                }
            })
        return Response({
            'is_authenticated': False
        })

# ========== Optional: Logout View for Session ==========
class SessionLogoutView(APIView):
    """
    Logout user and clear session
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        from django.contrib.auth import logout
        logout(request)
        return Response({
            'success': True,
            'message': 'Logged out successfully'
        })


class PasswordResetSMSRequestView(APIView):
    """Send a password reset code via SMS to the user's phone number."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = request.data.get('email') or request.data.get('phone')
        if not identifier:
            return Response({'error': 'Email or phone is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Try to find user by email or phone
        try:
            if '@' in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(phone=identifier)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if not user.phone:
            return Response({'error': 'User has no phone number'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate 6-digit code
        code = f"{random.randint(100000, 999999)}"
        expires_at = timezone.now() + timedelta(minutes=15)

        # Save code
        PasswordResetCode.objects.create(user=user, code=code, expires_at=expires_at)

        # Send SMS (prints in dev)
        message = f"Your Ankore Fresh password reset code is: {code}. Expires in 15 minutes."
        send_sms(str(user.phone), message)

        return Response({'message': 'Reset code sent via SMS'}, status=status.HTTP_200_OK)


class PasswordResetSMSConfirmView(APIView):
    """Verify code and set new password."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = request.data.get('email') or request.data.get('phone')
        code = request.data.get('code')
        new_password = request.data.get('new_password')

        if not identifier or not code or not new_password:
            return Response({'error': 'email/phone, code and new_password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if '@' in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(phone=identifier)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Find valid code
        now = timezone.now()
        try:
            pr = PasswordResetCode.objects.filter(user=user, code=code, used=False, expires_at__gte=now).latest('created_at')
        except PasswordResetCode.DoesNotExist:
            return Response({'error': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)

        # Set new password
        user.set_password(new_password)
        user.save()
        pr.used = True
        pr.save()

        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)