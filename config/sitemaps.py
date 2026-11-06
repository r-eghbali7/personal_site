from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import BlogPost
from courses.models import Course


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return [
            'courses:home',
            'courses:list',
            'courses:quiz_list',
            'blog:list',
            'podcasts:list',
        ]

    def location(self, item):
        return reverse(item)


class CourseSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Course.objects.filter(is_published=True).order_by('pk')

    def location(self, item):
        return reverse('courses:detail', kwargs={'slug': item.slug})

    def lastmod(self, item):
        return item.updated_at


class BlogPostSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return BlogPost.objects.filter(is_published=True).order_by('pk')

    def location(self, item):
        return reverse('blog:detail', kwargs={'slug': item.slug})

    def lastmod(self, item):
        return item.updated_at
