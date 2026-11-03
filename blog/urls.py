"""URLs: blog"""
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.BlogListView.as_view(), name='list'),
    path('<uslug:slug>/coupon/request/', views.BlogCouponRequestView.as_view(), name='coupon_request'),
    path('<uslug:slug>/coupon/verify/', views.BlogCouponVerifyView.as_view(), name='coupon_verify'),
    path('<uslug:slug>/', views.BlogDetailView.as_view(), name='detail'),
    path('<uslug:slug>/comment/', views.BlogCommentView.as_view(), name='comment'),
]
