"""Views: courses"""
import json
from urllib.parse import parse_qs, urlparse
from django.views import View
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.urls import reverse
from .models import Category, Course, Chapter, Lesson, Quiz, FinalProject


def prepare_chapter_media(chapters, user):
    for chapter in chapters:
        lessons = list(chapter.lessons.all())
        for lesson in lessons:
            lesson.can_play = lesson.can_access(user)
            lesson.player_kind = None
            lesson.player_url = ''
            if not lesson.can_play:
                continue
            if lesson.video_file:
                lesson.player_kind = 'video'
                lesson.player_url = lesson.video_file.url
                continue
            if not lesson.video_url:
                continue
            parsed_url = urlparse(lesson.video_url)
            host = parsed_url.hostname or ''
            path_parts = [part for part in parsed_url.path.split('/') if part]
            if host.endswith('youtu.be'):
                video_id = path_parts[0] if path_parts else ''
            elif host.endswith('youtube.com'):
                video_id = parse_qs(parsed_url.query).get('v', [''])[0]
                if not video_id and len(path_parts) > 1 and path_parts[0] in {'embed', 'shorts'}:
                    video_id = path_parts[1]
            else:
                video_id = ''
            if video_id:
                lesson.player_kind = 'embed'
                lesson.player_url = f'https://www.youtube-nocookie.com/embed/{video_id}'
            elif host.endswith('aparat.com'):
                video_hash = path_parts[-1] if path_parts else ''
                if path_parts and path_parts[0] == 'video' and len(path_parts) > 1:
                    video_hash = path_parts[-1]
                if video_hash:
                    lesson.player_kind = 'embed'
                    lesson.player_url = f'https://www.aparat.com/video/video/embed/videohash/{video_hash}/vt/frame'
        chapter.lesson_list = lessons
    return chapters

def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept','')

class HomeView(View):
    def get(self, request):
        courses = Course.objects.filter(is_published=True).select_related('category','instructor')
        categories = Category.objects.all()
        context = {'courses': courses, 'categories': categories}
        if is_ajax(request):
            return JsonResponse({'courses': [{'id':c.id,'title':c.title,'slug':c.slug,'price':str(c.price)} for c in courses], 'categories':[{'id':c.id,'name':c.name,'slug':c.slug} for c in categories]})
        return render(request, 'home.html', context)

class CourseListView(View):
    def get(self, request):
        qs = Course.objects.filter(is_published=True).select_related('category', 'instructor').annotate(
            chapter_count=Count('chapters', distinct=True),
            student_count=Count(
                'enrollments__user',
                filter=Q(enrollments__is_active=True),
                distinct=True,
            ),
        )
        cat = request.GET.get('category')
        if cat:
            qs = qs.filter(category__slug=cat)
        search_query = request.GET.get('q', '').strip()
        if search_query:
            qs = qs.filter(
                Q(title__icontains=search_query)
                | Q(short_description__icontains=search_query)
                | Q(description__icontains=search_query)
            )
        categories = Category.objects.annotate(
            course_count=Count('courses', filter=Q(courses__is_published=True), distinct=True),
        )
        stats = Course.objects.filter(is_published=True).aggregate(
            published_course_count=Count('id', distinct=True),
            student_count=Count(
                'enrollments__user',
                filter=Q(enrollments__is_active=True),
                distinct=True,
            ),
        )
        context = {
            'courses': qs,
            'categories': categories,
            'selected_category': cat or '',
            'search_query': search_query,
            'result_count': qs.count(),
            **stats,
        }
        if is_ajax(request):
            return JsonResponse({'courses':[{'id':c.id,'title':c.title,'slug':c.slug,'price':str(c.price),'level':c.level} for c in qs]})
        return render(request, 'list_course.html', context)


class QuizListView(View):
    def get(self, request):
        quizzes = Quiz.objects.filter(
            chapter__course__is_published=True,
        ).select_related('chapter__course')
        return render(request, 'quiz_list.html', {'quizzes': quizzes})

class CourseDetailView(View):
    def get(self, request, slug):
        course = get_object_or_404(
            Course.objects.select_related('category', 'instructor'),
            slug=slug,
            is_published=True,
        )
        chapters = prepare_chapter_media(
            course.chapters.prefetch_related('lessons', 'quiz').all(),
            request.user,
        )
        context = {
            'course': course,
            'chapters': chapters,
            'enrolled': course.is_enrolled(request.user),
            'final_project': FinalProject.objects.filter(course=course).first(),
            'related_courses': Course.objects.filter(
                is_published=True,
                category=course.category,
            ).exclude(pk=course.pk).select_related('category')[:3],
        }
        if is_ajax(request):
            return JsonResponse({'course':{'id':course.id,'title':course.title,'slug':course.slug,'price':str(course.price)},'chapters':[{'id':ch.id,'title':ch.title} for ch in chapters]})
        return render(request, 'detail_course.html', context)


class ChapterDetailView(View):
    def get(self, request, course_slug, chapter_id):
        course = get_object_or_404(
            Course.objects.select_related('instructor'),
            slug=course_slug,
            is_published=True,
        )
        chapter = get_object_or_404(
            Chapter.objects.prefetch_related('lessons', 'quiz'),
            pk=chapter_id,
            course=course,
        )
        prepare_chapter_media([chapter], request.user)
        context = {
            'course': course,
            'chapter': chapter,
            'chapters': course.chapters.all(),
            'enrolled': course.is_enrolled(request.user),
        }
        return render(request, 'chapter_detail.html', context)

class LessonView(View):
    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, slug=kwargs['course_slug'], is_published=True)
        self.lesson = get_object_or_404(
            Lesson,
            pk=kwargs['lesson_id'],
            chapter__course=self.course,
        )
        if not self.lesson.can_access(request.user):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('accounts:login')}?next={request.path}")
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, course_slug, lesson_id):
        course = self.course
        lesson = self.lesson
        context = {'course': course, 'lesson': lesson}
        if is_ajax(request):
            return JsonResponse({'lesson':{'id':lesson.id,'title':lesson.title,'video_url':lesson.video_url}})
        return render(request, 'lesson_detail.html', context)

class QuizView(LoginRequiredMixin, View):
    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        if not quiz.chapter.course.is_free and not quiz.chapter.course.is_enrolled(request.user):
            raise PermissionDenied
        questions = quiz.questions.prefetch_related('choices')
        context = {'quiz': quiz, 'questions': questions}
        if is_ajax(request):
            return JsonResponse({'quiz':{'id':quiz.id,'title':quiz.title,'pass_score':quiz.pass_score},'questions':[{'id':q.id,'body':q.body,'choices':[{'id':c.id,'text':c.text} for c in q.choices.all()]} for q in questions]})
        return render(request, 'quiz.html', context)

class QuizSubmitView(LoginRequiredMixin, View):
    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        if not quiz.chapter.course.is_free and not quiz.chapter.course.is_enrolled(request.user):
            raise PermissionDenied
        try:
            data = json.loads(request.body or '{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = request.POST
        answers = data.get('answers', {})
        if not isinstance(answers, dict):
            return JsonResponse({'error': 'answers must be an object'}, status=400)
        total = quiz.questions.count()
        correct = 0
        for q in quiz.questions.all():
            choice_id = answers.get(str(q.id))
            if choice_id:
                try:
                    correct += q.choices.filter(id=int(choice_id), is_correct=True).exists()
                except (TypeError, ValueError):
                    continue
        score = int((correct/total)*100) if total else 0
        from courses.models import QuizAttempt
        QuizAttempt.objects.create(user=request.user, quiz=quiz, score=score)
        return JsonResponse({'score': score, 'passed': score >= quiz.pass_score})

class FinalProjectView(LoginRequiredMixin, View):
    def get(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        if not course.is_free and not course.is_enrolled(request.user):
            raise PermissionDenied
        project = get_object_or_404(FinalProject, course=course)
        context = {'course': course, 'project': project}
        if is_ajax(request):
            return JsonResponse({'project':{'id':project.id,'title':project.title,'description':project.description}})
        return render(request, 'project.html', context)
    def post(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        if not course.is_free and not course.is_enrolled(request.user):
            raise PermissionDenied
        project = get_object_or_404(FinalProject, course=course)
        from courses.models import ProjectSubmission
        submitted_file = request.FILES.get('file')
        if not submitted_file:
            return JsonResponse({'error': 'a submission file is required'}, status=400)
        ProjectSubmission.objects.create(
            user=request.user,
            project=project,
            submitted_file=submitted_file,
            description=request.POST.get('description', ''),
        )
        return JsonResponse({'success': True})
