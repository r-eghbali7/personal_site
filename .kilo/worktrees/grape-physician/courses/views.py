"""Views: courses (stub)"""
from django.views import View
from django.shortcuts import render


class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')


class CourseListView(View):
    def get(self, request):
        return render(request, 'list_course.html')


class CourseDetailView(View):
    def get(self, request, slug):
        return render(request, 'detail_course.html')


class LessonView(View):
    def get(self, request, course_slug, lesson_id):
        return render(request, 'lesson_detail.html')


class QuizView(View):
    def get(self, request, quiz_id):
        return render(request, 'quiz.html')


class QuizSubmitView(View):
    def post(self, request, quiz_id):
        from django.shortcuts import redirect
        return redirect('courses:home')


class FinalProjectView(View):
    def get(self, request, course_slug):
        return render(request, 'project.html')

    def post(self, request, course_slug):
        from django.shortcuts import redirect
        return redirect('courses:home')
