"""URLs: podcasts — صفحه مستقل همه اپیزودهای پادکست."""

from django.urls import path

from . import views

app_name = 'podcasts'

urlpatterns = [
    path('', views.PodcastListView.as_view(), name='list'),
    path('<slug:slug>/like/', views.PodcastLikeToggleView.as_view(), name='like'),
    path('<slug:slug>/comment/', views.PodcastCommentCreateView.as_view(), name='comment'),
]
