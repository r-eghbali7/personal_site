"""
Django URL Configuration for LMS آکادمی طاهری
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('courses.urls')),
    path('accounts/', include('accounts.urls')),
    path('orders/', include('orders.urls')),
    path('tickets/', include('tickets.urls')),
    path('blog/', include('blog.urls')),
    path('search/', include('search.urls')),
]