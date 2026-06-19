from django.urls import path
from . import views

urlpatterns = [
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-code/', views.VerifyResetCodeView.as_view(), name='verify-code'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
]