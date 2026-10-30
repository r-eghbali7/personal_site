"""Views: site search"""
from django.views import View
from django.http import JsonResponse
from django.db.models import Q
from django.utils.safestring import mark_safe
from courses.models import Course
from blog.models import BlogPost
class SiteSearchView(View):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        if not q or len(q) < 2:
            return JsonResponse({'results': []})

        courses = Course.objects.filter(
            is_published=True
        ).filter(
            Q(title__icontains=q) | Q(short_description__icontains=q) | Q(description__icontains=q)
        ).only(
            'id', 'title', 'slug', 'short_description'
        ).order_by('-created_at')

        posts = BlogPost.objects.filter(
            is_published=True
        ).filter(
            Q(title__icontains=q) | Q(summary__icontains=q) | Q(content__icontains=q)
        ).only(
            'id', 'title', 'slug', 'summary'
        ).order_by('-published_at')

        results = []

        for course in courses:
            results.append({
                'kind': 'دوره',
                'title': course.title,
                'url': f'/courses/{course.slug}/',
                'summary': mark_safe(course.short_description[:150] + ('...' if course.short_description and len(course.short_description) > 150 else '')),
            })

        for post in posts:
            results.append({
                'kind': 'مقاله',
                'title': post.title,
                'url': f'/blog/{post.slug}/',
                'summary': mark_safe(post.summary[:150] + ('...' if post.summary and len(post.summary) > 150 else '')),
            })

        return JsonResponse({'results': results})