"""URLs: orders"""
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:course_id>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('payment/request/', views.PaymentRequestView.as_view(), name='payment_request'),
    path('payment/verify/', views.PaymentVerifyView.as_view(), name='payment_verify'),
    path('payment/success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('payment/failed/', views.PaymentFailedView.as_view(), name='payment_failed'),
]
