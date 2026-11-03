from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from django.conf import settings

from accounts.models import CustomUser
from accounts.models import OTPCode
from .models import (
	BlogCouponClaim,
	BlogPost,
	Comment,
	PodcastComment,
	PodcastLike,
)


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

	def test_comment_form_post_with_ajax_returns_json(self):
		self.client.force_login(self.user)

		response = self.client.post(
			reverse('blog:comment', kwargs={'slug': self.post.slug}),
			{'body': 'دیدگاه فرم آزمایشی'},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 200)
		self.assertIn('message', response.json())
		self.assertEqual(Comment.objects.count(), 1)

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
		self.assertTrue(response.json()['pending'])
		self.assertEqual(response.json()['level'], 'success')
		self.assertIn('پس از تأیید', response.json()['message'])
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


class PodcastPageTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			phone_number='09123334444',
			password='test-password-123',
			full_name='شنونده نمونه',
		)
		self.other_user = CustomUser.objects.create_user(
			phone_number='09123335555',
			password='test-password-123',
			full_name='شنونده دوم',
		)
		self.episode = BlogPost.objects.create(
			title='اپیزود پادکست اول',
			slug='podcast-episode-one',
			content='توضیح مقاله',
			author=self.user,
			podcast_title='برج مراقبت — قسمت اول',
			podcast_audio_url='https://media.example.test/one.mp3',
			podcast_duration_minutes=8,
			published_at=timezone.make_aware(datetime(2026, 4, 6, 12, 0)),
			is_published=True,
		)
		self.episode_two = BlogPost.objects.create(
			title='اپیزود پادکست دوم',
			slug='podcast-episode-two',
			content='توضیح مقاله دوم',
			author=self.user,
			podcast_title='شکست — قسمت سوم',
			podcast_audio_url='https://media.example.test/two.mp3',
			podcast_duration_minutes=12,
			is_published=True,
		)
		BlogPost.objects.create(
			title='مقاله بدون پادکست',
			slug='article-without-podcast',
			content='متن',
			author=self.user,
			is_published=True,
		)
		BlogPost.objects.create(
			title='اپیزود پیش‌نویس',
			slug='draft-podcast-episode',
			content='متن',
			author=self.user,
			podcast_audio_url='https://media.example.test/draft.mp3',
			is_published=False,
		)

	def test_page_lists_only_published_episodes_with_comments_and_likes(self):
		PodcastLike.objects.create(post=self.episode, user=self.user)
		PodcastComment.objects.create(post=self.episode, user=self.other_user, body='دیدگاه تأییدشده')
		PodcastComment.objects.create(
			post=self.episode,
			user=self.other_user,
			body='دیدگاه پنهان',
			is_approved=False,
		)

		response = self.client.get(reverse('podcasts:list'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.episode.podcast_title)
		self.assertContains(response, self.episode_two.podcast_title)
		self.assertNotContains(response, 'مقاله بدون پادکست')
		self.assertNotContains(response, 'اپیزود پیش‌نویس')
		self.assertContains(response, 'دیدگاه تأییدشده')
		self.assertNotContains(response, 'دیدگاه پنهان')
		self.assertContains(response, f'id="episode-{self.episode.pk}"', html=False)
		self.assertContains(response, 'podcast-seek')

		episode = next(post for post in response.context['posts'] if post.pk == self.episode.pk)
		self.assertEqual(episode.like_count, 1)
		self.assertEqual(episode.comment_count, 1)

	def test_like_requires_login_and_toggles_for_authenticated_user(self):
		like_url = reverse('podcasts:like', kwargs={'slug': self.episode.slug})

		anonymous = self.client.post(like_url)
		self.assertRedirects(
			anonymous,
			f"{reverse('accounts:login')}?next={reverse('podcasts:list')}",
		)
		self.assertFalse(PodcastLike.objects.exists())

		self.client.force_login(self.user)
		self.client.post(like_url)
		self.assertEqual(
			PodcastLike.objects.filter(post=self.episode, user=self.user).count(),
			1,
		)
		self.assertContains(self.client.get(reverse('podcasts:list')), 'aria-pressed="true"')

		self.client.post(like_url)
		self.assertFalse(PodcastLike.objects.exists())
		self.assertContains(self.client.get(reverse('podcasts:list')), 'aria-pressed="false"')

	def test_like_toggle_via_ajax_returns_updated_state_without_redirect(self):
		like_url = reverse('podcasts:like', kwargs={'slug': self.episode.slug})
		self.client.force_login(self.user)

		response = self.client.post(like_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json(), {
			'liked': True,
			'like_count': 1,
			'message': 'این اپیزود را پسندیدید.',
			'level': 'success',
		})

		response = self.client.post(like_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['liked'], False)
		self.assertEqual(response.json()['like_count'], 0)
		self.assertEqual(response.json()['level'], 'error')

	def test_ajax_like_requires_login(self):
		response = self.client.post(
			reverse('podcasts:like', kwargs={'slug': self.episode.slug}),
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 401)
		self.assertFalse(PodcastLike.objects.exists())

	def test_comment_via_ajax_returns_html_and_updated_count(self):
		self.client.force_login(self.user)

		response = self.client.post(
			reverse('podcasts:comment', kwargs={'slug': self.episode.slug}),
			{'body': 'دیدگاه آزمایشی پادکست'},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertEqual(data['level'], 'success')
		self.assertEqual(data['comment_count'], 1)
		self.assertIn('دیدگاه آزمایشی پادکست', data['html'])
		self.assertIn('شنونده نمونه', data['html'])
		self.assertEqual(PodcastComment.objects.count(), 1)

	def test_ajax_comment_requires_login_for_podcast(self):
		response = self.client.post(
			reverse('podcasts:comment', kwargs={'slug': self.episode.slug}),
			{'body': 'دیدگاه مهمان'},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 401)
		self.assertFalse(PodcastComment.objects.exists())

	def test_podcast_page_includes_ajax_comment_assets(self):
		self.client.force_login(self.user)
		response = self.client.get(reverse('podcasts:list'))

		self.assertContains(response, 'ajax-comment-form')
		self.assertContains(response, 'comments.js')
		self.assertContains(response, f'comments-list-{self.episode.pk}')

	def test_action_feedback_is_rendered_as_toast(self):
		self.client.force_login(self.user)

		response = self.client.post(
			reverse('podcasts:comment', kwargs={'slug': self.episode.slug}),
			{'body': 'دیدگاه برای تست توست'},
			follow=True,
		)

		html = response.content.decode()
		self.assertContains(response, 'id="toast-container"', html=False, count=1)
		self.assertContains(response, 'border-green-200', html=False)
		self.assertContains(response, 'fixed right-4 top-20', html=False)
		self.assertContains(response, 'toasts.js')
		self.assertIn('@keyframes toast-in', html)
		self.assertIn('@keyframes toast-out', html)
		self.assertEqual(html.count('دیدگاه شما ثبت شد.'), 1)

	def test_comment_requires_login_and_is_created_for_authenticated_user(self):
		comment_url = reverse('podcasts:comment', kwargs={'slug': self.episode.slug})

		self.client.post(comment_url, {'body': 'نظر مهمان'})
		self.assertFalse(PodcastComment.objects.exists())

		self.client.force_login(self.other_user)
		response = self.client.post(comment_url, {'body': 'نظر کاربر'})

		self.assertEqual(
			response.url,
			f"{reverse('podcasts:list')}#episode-{self.episode.pk}",
		)
		comment = PodcastComment.objects.get()
		self.assertEqual(comment.body, 'نظر کاربر')
		self.assertEqual(comment.user, self.other_user)

		self.client.post(comment_url, {'body': ' '})
		self.assertEqual(PodcastComment.objects.count(), 1)

	def test_page_shows_login_prompt_for_guest(self):
		response = self.client.get(reverse('podcasts:list'))

		self.assertContains(response, 'برای ثبت دیدگاه')
		self.assertContains(response, 'برای پسندیدن وارد شوید')

	def test_comments_box_is_hidden_until_episode_is_played(self):
		response = self.client.get(reverse('podcasts:list'))

		self.assertContains(response, 'podcast-comments')
		self.assertContains(response, 'podcast-comments-box')

		css = (Path(settings.BASE_DIR) / 'static' / 'css' / 'podcast-player.css').read_text(encoding='utf-8')
		self.assertIn('.podcast-list-page .podcast-comments', css)
		self.assertIn('.podcast-list-page .podcast-card.is-active .podcast-comments', css)
		self.assertIn('grid-template-rows: 0fr', css)
		self.assertIn('transition:', css)


class BlogContentTocTests(TestCase):
	def test_headings_get_unique_ids_and_toc_entries(self):
		from .content import article_content_and_toc

		html, toc = article_content_and_toc(
			'<h2>مقدمه و شروع</h2><p>متن</p>'
			'<h2>مقدمه و شروع</h2>'
			'<h3>زیربخش مهم</h3>'
		)

		self.assertEqual([item['text'] for item in toc], [
			'مقدمه و شروع',
			'مقدمه و شروع',
			'زیربخش مهم',
		])
		self.assertEqual([item['level'] for item in toc], [2, 2, 3])
		self.assertEqual(len({item['id'] for item in toc}), 3)
		for item in toc:
			self.assertIn(f'id="{item["id"]}"', html)

	def test_plain_text_content_still_renders_with_line_breaks(self):
		from .content import article_content_and_toc

		html, toc = article_content_and_toc('خط اول\nخط دوم')

		self.assertEqual(toc, [])
		self.assertIn('خط اول', html)
		self.assertIn('خط دوم', html)
		self.assertIn('<br', html)

	def test_article_page_renders_dynamic_toc_and_editor_html(self):
		user = CustomUser.objects.create_user(
			phone_number='09125551010',
			password='test-password-123',
		)
		post = BlogPost.objects.create(
			title='مقاله با سرفصل',
			slug='article-with-headings',
			content=(
				'<h2>بخش اول مقاله</h2>'
				'<p>متن <strong>مهم</strong> بخش اول.</p>'
				'<h3>جزئیات بخش اول</h3>'
				'<p>توضیح بیشتر.</p>'
			),
			author=user,
			is_published=True,
		)

		response = self.client.get(reverse('blog:detail', kwargs={'slug': post.slug}))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'فهرست سرفصل‌های مقاله')
		self.assertContains(response, 'بخش اول مقاله')
		self.assertContains(response, 'جزئیات بخش اول')
		self.assertContains(response, 'class="article-body')
		self.assertContains(response, '<strong>مهم</strong>', html=False)

		toc = response.context['toc']
		self.assertEqual(len(toc), 2)
		for item in toc:
			self.assertContains(response, f'href="#{item["id"]}"', html=False)

	def test_toc_links_are_generated_in_page_order(self):
		user = CustomUser.objects.create_user(
			phone_number='09125551011',
			password='test-password-123',
		)
		post = BlogPost.objects.create(
			title='مقاله ترتیب سرفصل',
			slug='article-toc-order',
			content='<h2>اول</h2><p>الف</p><h2>دوم</h2><p>ب</p>',
			author=user,
			is_published=True,
		)

		response = self.client.get(reverse('blog:detail', kwargs={'slug': post.slug}))
		toc = response.context['toc']

		self.assertEqual([item['text'] for item in toc], ['اول', 'دوم'])
		html = response.content.decode()
		self.assertLess(html.index('href="#' + toc[0]['id'] + '"'), html.index('href="#' + toc[1]['id'] + '"'))


class BlogEditorAdminTests(TestCase):
	def setUp(self):
		self.admin_user = CustomUser.objects.create_superuser(
			phone_number='09125551012',
			password='admin-password-123',
		)
		self.client.force_login(self.admin_user)

	def test_blog_content_uses_ckeditor5_field_with_extends_config(self):
		from django_ckeditor_5.widgets import CKEditor5Widget

		field = BlogPost._meta.get_field('content')

		self.assertEqual(field.get_internal_type(), 'TextField')
		self.assertEqual(field.config_name, 'extends')
		self.assertIsInstance(field.formfield().widget, CKEditor5Widget)
		self.assertEqual(field.formfield().widget.config.get('language'), 'fa')
		self.assertFalse(field.formfield().widget._config_errors)

		add_page = self.client.get(reverse('admin:blog_blogpost_add'))
		self.assertEqual(add_page.status_code, 200)
		self.assertContains(add_page, 'django_ckeditor_5')
		self.assertContains(add_page, 'ckeditor')

	def test_ckeditor_extends_config_and_upload_are_ready(self):
		from django.conf import settings
		from django.urls import reverse as url_reverse

		self.assertIn('extends', settings.CKEDITOR_5_CONFIGS)
		toolbar_items = settings.CKEDITOR_5_CONFIGS['extends']['toolbar']['items']
		self.assertIn('mediaEmbed', toolbar_items)
		self.assertIn('htmlEmbed', toolbar_items)
		self.assertIn('insertImage', toolbar_items)
		self.assertTrue(url_reverse('ck_editor_5_upload_file'))
		self.assertEqual(settings.CKEDITOR_5_FILE_UPLOAD_PERMISSION, 'staff')


class BlogCommentCsrfTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			phone_number='09124446666',
			password='test-password-123',
			full_name='نویسنده نظر',
		)
		self.post = BlogPost.objects.create(
			title='CSRF comment post',
			slug='csrf-comment-post',
			content='متن مقاله',
			author=self.user,
			is_published=True,
		)

	def test_ajax_comment_accepts_csrf_token_from_article_page(self):
		client = Client(enforce_csrf_checks=True)
		client.force_login(self.user)
		page = client.get(reverse('blog:detail', kwargs={'slug': self.post.slug}))

		self.assertEqual(page.status_code, 200)
		cookie = client.cookies.get('csrftoken')
		self.assertIsNotNone(cookie, 'CSRF cookie must be set on the article page')

		response = client.post(
			reverse('blog:comment', kwargs={'slug': self.post.slug}),
			{'body': 'نظر با توکن CSRF', 'csrfmiddlewaretoken': cookie.value},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
			HTTP_REFERER=f"http://testserver{page.request['PATH_INFO']}",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(Comment.objects.count(), 1)
