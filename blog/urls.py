"""URLs: blog"""
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.BlogListView.as_view(), name='list'),
    path('<slug:slug>/coupon/request/', views.BlogCouponRequestView.as_view(), name='coupon_request'),
    path('<slug:slug>/coupon/verify/', views.BlogCouponVerifyView.as_view(), name='coupon_verify'),
    path('<slug:slug>/', views.BlogDetailView.as_view(), name='detail'),
    path('<slug:slug>/comment/', views.BlogCommentView.as_view(), name='comment'),
]
