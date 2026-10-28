from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views import View

from blog.models import BlogPost
from courses.models import Course


class SiteSearchView(View):
    def get(self, request):
        query = request.GET.get('q', '').strip()[:100]
        if len(query) < 2:
            return JsonResponse({'results': []})

        courses = Course.objects.filter(is_published=True).filter(
            Q(title__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
        ).order_by('title')[:5]
        posts = BlogPost.objects.filter(is_published=True).filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query)
        ).order_by('-published_at', '-created_at')[:5]

        results = [
            {
                'title': course.title,
                'summary': course.short_description,
                'kind': 'دوره',
                'url': reverse('courses:detail', kwargs={'slug': course.slug}),
            }
            for course in courses
        ]
        results.extend(
            {
                'title': post.title,
                'summary': post.summary,
                'kind': 'مقاله',
                'url': reverse('blog:detail', kwargs={'slug': post.slug}),
            }
            for post in posts
        )
        return JsonResponse({'results': results[:8]})