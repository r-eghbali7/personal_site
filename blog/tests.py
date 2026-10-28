from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from .models import BlogPost, Comment


class BlogFlowTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			phone_number='09126667777',
			password='test-password-123',
			full_name='Blog Reader',
		)
		self.post = BlogPost.objects.create(
			title='Database-backed article',
			slug='database-backed-article',
			summary='Article summary',
			content='Article content from the database.',
			author=self.user,
			is_published=True,
		)

	def test_detail_renders_post_content_and_counts_views(self):
		response = self.client.get(reverse('blog:detail', kwargs={'slug': self.post.slug}))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.post.title)
		self.assertContains(response, self.post.content)
		self.post.refresh_from_db()
		self.assertEqual(self.post.views_count, 1)

	def test_blog_list_renders_published_posts(self):
		response = self.client.get(reverse('blog:list'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.post.title)

	def test_comment_requires_login_and_json_post_is_moderated(self):
		comment_url = reverse('blog:comment', kwargs={'slug': self.post.slug})
		anonymous_response = self.client.post(comment_url, {'body': 'A useful comment'})
		self.assertEqual(anonymous_response.status_code, 302)
		self.assertFalse(Comment.objects.exists())

		self.client.force_login(self.user)
		response = self.client.post(
			comment_url,
			data='{"body":"A useful comment"}',
			content_type='application/json',
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()['success'])
		self.assertFalse(Comment.objects.get().is_approved)
