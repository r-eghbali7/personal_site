"""URLs: courses"""
from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('courses/', views.CourseListView.as_view(), name='list'),
    path('courses/<slug:slug>/', views.CourseDetailView.as_view(), name='detail'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/', views.LessonView.as_view(), name='lesson'),
    path('quiz/<int:quiz_id>/', views.QuizView.as_view(), name='quiz'),
    path('quiz/<int:quiz_id>/submit/', views.QuizSubmitView.as_view(), name='quiz_submit'),
    path('courses/<slug:course_slug>/project/', views.FinalProjectView.as_view(), name='project'),
]
