from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from blog.models import BlogPost
from courses.models import Course


class SiteSearchTests(TestCase):
    def setUp(self):
        author = CustomUser.objects.create_user(
            phone_number='09127770000',
            password='test-password-123',
        )
        self.course = Course.objects.create(
            title='Django Search Course',
            slug='django-search-course',
            description='Searchable course content',
            short_description='A course for search tests',
            is_published=True,
            instructor=author,
        )
        self.post = BlogPost.objects.create(
            title='Django Search Article',
            slug='django-search-article',
            summary='Searchable article summary',
            content='Article text',
            author=author,
            is_published=True,
        )
        self.url = reverse('site_search')

    def test_search_returns_published_courses_and_articles(self):
        response = self.client.get(self.url, {'q': 'Django'})

        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        self.assertEqual({result['kind'] for result in results}, {'دوره', 'مقاله'})
        self.assertEqual(
            {result['url'] for result in results},
            {
                reverse('courses:detail', kwargs={'slug': self.course.slug}),
                reverse('blog:detail', kwargs={'slug': self.post.slug}),
            },
        )

    def test_short_query_returns_empty_results(self):
        response = self.client.get(self.url, {'q': 'D'})

        self.assertEqual(response.json(), {'results': []})

    def test_header_routes_render_on_blog_list(self):
        response = self.client.get(reverse('blog:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'site-header.js')
        self.assertContains(response, 'data-path="courses"')
        self.assertContains(response, 'shopping_bag')
