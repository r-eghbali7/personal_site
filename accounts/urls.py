"""URLs: accounts — با OTPResendView جدید"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('forgot-password/', views.ForgotPasswordRequestView.as_view(), name='forgot_password'),
    path('otp/', views.OTPVerifyView.as_view(), name='otp_verify'),
    path('otp/resend/', views.OTPResendView.as_view(), name='otp_resend'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('newsletter/subscribe/', views.NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),
]
