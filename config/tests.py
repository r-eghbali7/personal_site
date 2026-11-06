from xml.etree import ElementTree

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


class SeoEndpointTests(TestCase):
    def setUp(self):
        self.author = CustomUser.objects.create_user(
            phone_number='09127770001',
            password='test-password-123',
        )
        self.course = Course.objects.create(
            title='Published SEO Course',
            slug='published-seo-course',
            description='Course description',
            short_description='Course search description',
            is_published=True,
            instructor=self.author,
        )
        self.post = BlogPost.objects.create(
            title='Published SEO Article',
            slug='published-seo-article',
            summary='Article search description',
            content='Article body',
            author=self.author,
            is_published=True,
        )
        Course.objects.create(
            title='Draft SEO Course',
            slug='draft-seo-course',
            description='Draft course',
            instructor=self.author,
        )
        BlogPost.objects.create(
            title='Draft SEO Article',
            slug='draft-seo-article',
            content='Draft article',
            author=self.author,
        )

    def test_robots_txt_lists_sitemap_and_excludes_private_routes(self):
        response = self.client.get(reverse('robots_txt'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertContains(response, 'Sitemap: http://testserver/sitemap.xml')
        self.assertContains(response, 'Disallow: /accounts/')
        self.assertContains(response, 'Disallow: /orders/')
        self.assertContains(response, 'Disallow: /tickets/')

    def test_sitemap_contains_public_pages_and_published_content_only(self):
        response = self.client.get(reverse('sitemap'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('application/xml', response['Content-Type'])
        root = ElementTree.fromstring(response.content)
        locations = {
            element.text
            for element in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        }

        self.assertIn('http://testserver/', locations)
        self.assertIn('http://testserver/courses/', locations)
        self.assertIn(
            f'http://testserver/courses/{self.course.slug}/',
            locations,
        )
        self.assertIn(f'http://testserver/blog/{self.post.slug}/', locations)
        self.assertNotIn('http://testserver/courses/draft-seo-course/', locations)
        self.assertNotIn('http://testserver/blog/draft-seo-article/', locations)

    def test_detail_pages_render_canonical_and_content_specific_metadata(self):
        course_response = self.client.get(
            reverse('courses:detail', kwargs={'slug': self.course.slug}),
            {'source': 'newsletter'},
        )
        article_response = self.client.get(
            reverse('blog:detail', kwargs={'slug': self.post.slug}),
        )

        self.assertContains(
            course_response,
            f'<link rel="canonical" href="http://testserver/courses/{self.course.slug}/" />',
            html=True,
        )
        self.assertContains(course_response, 'Course search description')
        self.assertContains(course_response, '<meta property="og:type" content="website" />', html=True)
        self.assertContains(article_response, f'<title>{self.post.title} | آکادمی پارسا اقبالی</title>', html=True)
        self.assertContains(article_response, '<meta property="og:type" content="article" />', html=True)
        self.assertContains(article_response, 'Article search description')
