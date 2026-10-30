"""URLs: search"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.SiteSearchView.as_view(), name='site_search'),
]