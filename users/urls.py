from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Existing JWT endpoints
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('favorites/', views.FavoritesListCreateView.as_view(), name='favorites'),
    path('favorites/<str:product_id>/', views.FavoriteDeleteView.as_view(), name='favorite_delete'),
    path('password/change/', views.ChangePasswordView.as_view(), name='password_change'),
    
    # NEW: Mobile session authentication endpoints
    path('mobile-login/', views.MobileLoginView.as_view(), name='mobile-login'),
    path('session-status/', views.SessionStatusView.as_view(), name='session-status'),
    path('session-logout/', views.SessionLogoutView.as_view(), name='session-logout'),
    # Password reset via SMS
    path('password-reset/sms/', views.PasswordResetSMSRequestView.as_view(), name='password-reset-sms'),
    path('password-reset/sms/confirm/', views.PasswordResetSMSConfirmView.as_view(), name='password-reset-sms-confirm'),
    # Password reset via Email (OTP)
    path('password-reset/email/', views.PasswordResetEmailRequestView.as_view(), name='password-reset-email'),
    path('password-reset/email/confirm/', views.PasswordResetEmailConfirmView.as_view(), name='password-reset-email-confirm'),
]