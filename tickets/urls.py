"""URLs: tickets"""
from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.TicketListView.as_view(), name='list'),
    path('create/', views.TicketCreateView.as_view(), name='create'),
    path('<int:pk>/', views.TicketDetailView.as_view(), name='detail'),
    path('consultation/request/', views.ConsultationRequestView.as_view(), name='consultation_request'),
    path('consultation/send-otp/', views.SendOTPView.as_view(), name='send_otp'),
    path('consultation/verify-otp/', views.VerifyOTPView.as_view(), name='verify_otp'),
]
