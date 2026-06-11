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
from .email_service import send_password_reset_email
from django.utils import timezone
from datetime import timedelta
import random
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from .models import Favorite
from .serializers import FavoriteSerializer, ChangePasswordSerializer

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
        
        # Authenticate user using the configured USERNAME_FIELD (email)
        user = authenticate(request, username=email, password=password)
        
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


class PasswordResetEmailRequestView(APIView):
    """Send a password reset code via email to the user's email address."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Generate 6-digit code
        code = f"{random.randint(100000, 999999)}"
        expires_at = timezone.now() + timedelta(minutes=15)
        PasswordResetCode.objects.create(user=user, code=code, expires_at=expires_at)

        # Send email (prints in dev)
        ok = send_password_reset_email(user, code)
        if ok:
            return Response({'message': 'Reset code sent via email'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Reset code saved; failed to send email (check logs)'}, status=status.HTTP_200_OK)


class PasswordResetEmailConfirmView(APIView):
    """Verify code sent by email and set a new password."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')

        if not email or not code or not new_password:
            return Response({'error': 'email, code and new_password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        try:
            pr = PasswordResetCode.objects.filter(user=user, code=code, used=False, expires_at__gte=now).latest('created_at')
        except PasswordResetCode.DoesNotExist:
            return Response({'error': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        pr.used = True
        pr.save()

        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)


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


class FavoritesListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favs = Favorite.objects.filter(user=request.user).order_by('-created_at')
        serializer = FavoriteSerializer(favs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = FavoriteSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            fav, created = Favorite.objects.get_or_create(user=request.user, product_id=product_id)
            return Response({'product_id': fav.product_id, 'created': created}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FavoriteDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        try:
            fav = Favorite.objects.get(user=request.user, product_id=product_id)
            fav.delete()
            return Response({'deleted': True})
        except Favorite.DoesNotExist:
            return Response({'deleted': False}, status=status.HTTP_404_NOT_FOUND)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        old = serializer.validated_data['old_password']
        new = serializer.validated_data['new_password']
        user = request.user
        if not user.check_password(old):
            return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new)
        user.save()
        return Response({'message': 'Password changed successfully'})