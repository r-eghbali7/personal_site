from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from accounts.models import CustomUser
from accounts.models import OTPCode
from .models import BlogCouponClaim, BlogPost, Comment


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
		self.assertContains(response, self.post.summary)
		self.assertContains(response, '5 دقیقه مطالعه')
		self.assertNotContains(response, '{{ post.read_time_minutes }}')
		self.assertNotContains(response, '{{ post.summary|default:post.content|truncatechars:180')
		self.assertContains(response, self.post.content)
		self.post.refresh_from_db()
		self.assertEqual(self.post.views_count, 1)

	def test_blog_list_renders_published_posts(self):
		response = self.client.get(reverse('blog:list'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.post.title)

	def test_blog_list_filters_by_database_category_and_all_articles_link(self):
		self.post.category = 'بک‌اند و سیستم‌های توزیع‌شده'
		self.post.save(update_fields=['category'])
		other_post = BlogPost.objects.create(
			title='Frontend article',
			slug='frontend-article',
			content='Frontend content',
			author=self.user,
			category='فرانت‌اند و React/Next.js',
			is_published=True,
		)

		filtered = self.client.get(reverse('blog:list'), {'category': self.post.category})
		all_posts = self.client.get(reverse('blog:list'))

		self.assertEqual(filtered.status_code, 200)
		self.assertContains(filtered, self.post.title)
		self.assertNotContains(filtered, other_post.title)
		self.assertEqual(list(filtered.context['categories']), [
			'بک‌اند و سیستم‌های توزیع‌شده',
			'فرانت‌اند و React/Next.js',
		])
		self.assertEqual(list(all_posts.context['posts']), [other_post, self.post])

	def test_blog_list_paginates_nine_posts_and_reports_database_counts(self):
		for index in range(1, 11):
			BlogPost.objects.create(
				title=f'Pagination article {index}',
				slug=f'pagination-article-{index}',
				content='Pagination content',
				author=self.user,
				category='Engineering',
				is_published=True,
			)
		BlogPost.objects.create(
			title='Draft article',
			slug='draft-article',
				content='Draft content',
			author=self.user,
				category='Drafts',
				is_published=False,
		)

		first_page = self.client.get(reverse('blog:list'))
		second_page = self.client.get(reverse('blog:list'), {'page': 2})

		self.assertEqual(first_page.context['article_count'], 11)
		self.assertEqual(first_page.context['category_count'], 1)
		self.assertEqual(len(first_page.context['posts']), 9)
		self.assertEqual(first_page.context['page_obj'].number, 1)
		self.assertEqual(len(second_page.context['posts']), 2)
		self.assertEqual(second_page.context['page_obj'].number, 2)
		self.assertNotContains(first_page, 'خواننده ماهانه')
		self.assertContains(first_page, 'تعداد دسته‌بندی‌ها')
		self.assertNotContains(first_page, 'خبرنامه مهندسی نرم‌افزار')
		self.assertNotContains(first_page, 'پربازدیدترین مقالات ماه')
		self.assertNotContains(first_page, 'موضوعات داغ و کلیدواژه‌ها')
		self.assertNotContains(first_page, 'میزان تسلط شما به معماری نرم‌افزار چقدر است؟')
		self.assertNotContains(first_page, 'معماری سیستم‌های Event-Driven')
		self.assertContains(first_page, 'md:grid-cols-2 xl:grid-cols-3')
		self.assertContains(first_page, '<main class="flex flex-col gap-8">', html=False)

	def test_blog_category_pagination_keeps_selected_category(self):
		for index in range(10):
			BlogPost.objects.create(
				title=f'Backend article {index}',
				slug=f'backend-article-{index}',
				content='Backend content',
				author=self.user,
				category='Backend',
				is_published=True,
			)
		BlogPost.objects.create(
			title='Frontend article',
			slug='category-frontend-article',
			content='Frontend content',
			author=self.user,
				category='Frontend',
			is_published=True,
		)

		response = self.client.get(reverse('blog:list'), {'category': 'Backend', 'page': 2})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['page_obj'].paginator.count, 10)
		self.assertEqual(len(response.context['posts']), 1)
		self.assertContains(response, '?category=Backend&amp;page=1')
		self.assertNotContains(response, 'Frontend article')

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

	def test_article_quiz_is_configured_per_post_and_podcast_is_optional(self):
		self.post.architecture_quiz_title = 'آزمون طراحی معماری توزیع‌شده'
		self.post.architecture_quiz_description = 'دانسته‌های خود را درباره پیام‌رسان‌ها بسنجید.'
		self.post.podcast_title = 'گفت‌وگو درباره صف پیام'
		self.post.podcast_description = 'یک اپیزود کوتاه درباره انتخاب broker.'
		self.post.podcast_audio_url = 'https://media.example.test/episode.mp3'
		self.post.podcast_duration_minutes = 18
		self.post.save()

		response = self.client.get(reverse('blog:detail', kwargs={'slug': self.post.slug}))
		self.assertContains(response, self.post.architecture_quiz_title)
		self.assertContains(response, self.post.podcast_title)
		self.assertContains(response, self.post.podcast_audio_url)

		self.post.podcast_title = ''
		self.post.podcast_audio_url = ''
		self.post.save(update_fields=['podcast_title', 'podcast_audio_url'])
		response = self.client.get(reverse('blog:detail', kwargs={'slug': self.post.slug}))
		self.assertNotContains(response, 'رادیو کدرز (اپیزود مرتبط)')

	def test_unregistered_phone_receives_otp_then_persisted_coupon(self):
		phone = '09125550123'
		self.post.coupon_discount_percent = 15
		self.post.save(update_fields=['coupon_discount_percent'])
		request_url = reverse('blog:coupon_request', kwargs={'slug': self.post.slug})
		verify_url = reverse('blog:coupon_verify', kwargs={'slug': self.post.slug})

		with patch('blog.views.send_otp_code', return_value={'success': True, 'message': 'sent'}) as send_sms:
			response = self.client.post(request_url, {'phone_number': phone})

		self.assertRedirects(response, reverse('blog:detail', kwargs={'slug': self.post.slug}))
		send_sms.assert_called_once()
		otp = OTPCode.objects.get(phone_number=phone, is_used=False)
		response = self.client.get(reverse('blog:detail', kwargs={'slug': self.post.slug}))
		self.assertContains(response, 'id="coupon-otp-box"', html=False)
		self.assertContains(response, 'کد تأیید')

		response = self.client.post(verify_url, {'otp_code': otp.code}, follow=True)
		self.assertEqual(response.status_code, 200)
		claim = BlogCouponClaim.objects.get(phone_number=phone)
		self.assertEqual(claim.discount_percent, 15)
		self.assertContains(response, claim.coupon_code)
		otp.refresh_from_db()
		self.assertTrue(otp.is_used)

	def test_registered_phone_does_not_receive_blog_coupon_otp(self):
		registered = CustomUser.objects.create_user(phone_number='09125550999', password='test-password-123')
		request_url = reverse('blog:coupon_request', kwargs={'slug': self.post.slug})

		with patch('blog.views.send_otp_code') as send_sms:
			response = self.client.post(request_url, {'phone_number': registered.phone_number})

		self.assertRedirects(response, reverse('blog:detail', kwargs={'slug': self.post.slug}))
		send_sms.assert_not_called()
		self.assertFalse(OTPCode.objects.filter(phone_number=registered.phone_number).exists())
