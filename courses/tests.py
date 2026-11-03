from datetime import datetime

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser
from blog.models import BlogPost
from .models import (
	Category,
	Chapter,
	Course,
	CourseComment,
	Enrollment,
	FinalProject,
	Lesson,
	Quiz,
)


class CourseAccessTests(TestCase):
	def setUp(self):
		self.instructor = CustomUser.objects.create_user(
			phone_number='09120000001',
			password='test-password-123',
		)
		self.student = CustomUser.objects.create_user(
			phone_number='09120000002',
			password='test-password-123',
		)
		category = Category.objects.create(name='Test', slug='test')
		self.paid_course = Course.objects.create(
			title='Paid course',
			slug='paid-course',
			description='Description',
			price=1000,
			is_published=True,
			category=category,
			instructor=self.instructor,
		)
		self.chapter = Chapter.objects.create(course=self.paid_course, title='Chapter')
		self.preview = Lesson.objects.create(
			chapter=self.chapter,
			title='Preview',
			is_free_preview=True,
		)
		self.locked_lesson = Lesson.objects.create(chapter=self.chapter, title='Locked')
		self.quiz = Quiz.objects.create(chapter=self.chapter, title='Quiz')

	def test_anonymous_user_can_access_preview_but_not_paid_lesson(self):
		preview_response = self.client.get(
			reverse(
				'courses:lesson',
				kwargs={'course_slug': self.paid_course.slug, 'lesson_id': self.preview.id},
			),
			HTTP_ACCEPT='application/json',
		)
		locked_response = self.client.get(reverse(
			'courses:lesson',
			kwargs={'course_slug': self.paid_course.slug, 'lesson_id': self.locked_lesson.id},
		))

		self.assertEqual(preview_response.status_code, 200)
		self.assertEqual(preview_response.json()['lesson']['id'], self.preview.id)
		self.assertRedirects(
			locked_response,
			f"{reverse('accounts:login')}?next={locked_response.request['PATH_INFO']}",
		)

	def test_course_detail_renders_database_title_price_and_chapters(self):
		response = self.client.get(reverse('courses:detail', kwargs={'slug': self.paid_course.slug}))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.paid_course.title)
		self.assertContains(response, self.chapter.title)
		self.assertContains(response, '1000')

	def test_course_landing_content_and_inline_videos_are_database_backed(self):
		self.paid_course.learning_outcomes = ['طراحی API اختصاصی']
		self.paid_course.landing_sections = [
			{'title': 'پیش‌نیازهای این دوره', 'body': 'آشنایی با Python'},
		]
		self.paid_course.save(update_fields=['learning_outcomes', 'landing_sections'])
		self.preview.video_url = 'https://youtu.be/example-video'
		self.preview.duration_seconds = 121
		self.preview.save(update_fields=['video_url', 'duration_seconds'])

		response = self.client.get(reverse('courses:detail', kwargs={'slug': self.paid_course.slug}))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'طراحی API اختصاصی')
		self.assertContains(response, 'پیش‌نیازهای این دوره')
		self.assertContains(response, 'https://www.youtube-nocookie.com/embed/example-video')
		self.assertContains(response, '3 دقیقه')
		self.assertContains(response, reverse(
			'courses:chapter_detail',
			kwargs={'course_slug': self.paid_course.slug, 'chapter_id': self.chapter.id},
		))
		self.assertContains(response, 'data-course-tab="panel-about"')
		self.assertNotContains(response, 'href="#about"')

	def test_course_curriculum_chapters_start_collapsed(self):
		response = self.client.get(reverse('courses:detail', kwargs={'slug': self.paid_course.slug}))
		html = response.content.decode()

		self.assertEqual(response.status_code, 200)
		self.assertIn('chapter-accordion', html)
		self.assertIn('<summary', html)
		self.assertNotIn('<details class="group chapter-accordion" open', html)

	def test_chapter_landing_shows_only_its_lessons_and_inline_players(self):
		self.chapter.description = 'شرح این فصل'
		self.chapter.save(update_fields=['description'])
		self.preview.video_url = 'https://www.youtube.com/watch?v=chapter-video'
		self.preview.duration_seconds = 60
		self.preview.save(update_fields=['video_url', 'duration_seconds'])

		response = self.client.get(reverse(
			'courses:chapter_detail',
			kwargs={'course_slug': self.paid_course.slug, 'chapter_id': self.chapter.id},
		))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'شرح این فصل')
		self.assertContains(response, self.preview.title)
		self.assertContains(response, 'https://www.youtube-nocookie.com/embed/chapter-video')
		self.assertContains(response, '1 دقیقه')
		self.assertContains(response, self.locked_lesson.title)
		self.assertContains(response, 'برای پخش این ویدئو ابتدا در دوره ثبت‌نام کنید.')
		self.assertNotContains(response, reverse(
			'courses:lesson',
			kwargs={'course_slug': self.paid_course.slug, 'lesson_id': self.preview.id},
		))

	def test_home_and_course_list_render_published_courses(self):
		home_response = self.client.get(reverse('courses:home'))
		list_response = self.client.get(reverse('courses:list'))

		self.assertEqual(home_response.status_code, 200)
		self.assertContains(home_response, self.paid_course.title)
		self.assertEqual(list_response.status_code, 200)
		self.assertContains(list_response, self.paid_course.title)

	def test_course_list_uses_database_search_and_active_enrollment_counts(self):
		Enrollment.objects.create(user=self.student, course=self.paid_course)
		Enrollment.objects.create(user=self.instructor, course=self.paid_course, is_active=False)
		url = reverse('courses:list')

		response = self.client.get(url, {'category': 'test', 'q': 'Paid'})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['result_count'], 1)
		self.assertEqual(response.context['published_course_count'], 1)
		self.assertEqual(response.context['student_count'], 1)
		self.assertEqual(response.context['courses'][0].student_count, 1)
		self.assertEqual(response.context['courses'][0].chapter_count, 1)
		self.assertContains(response, reverse('courses:home'))
		self.assertNotContains(response, 'مرتب‌سازی:')
		self.assertNotContains(response, 'صفحه‌بندی دوره‌ها')

	def test_course_list_empty_state_does_not_render_sample_courses(self):
		response = self.client.get(reverse('courses:list'), {'q': 'not-a-real-course'})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['result_count'], 0)
		self.assertContains(response, 'دوره‌ای برای این جستجو یا دسته‌بندی پیدا نشد.')
		self.assertNotContains(response, 'دوره جامع مسترکلاس Next.js 15')

	def test_non_enrolled_user_cannot_open_or_submit_paid_quiz(self):
		self.client.force_login(self.student)
		quiz_url = reverse('courses:quiz', kwargs={'quiz_id': self.quiz.id})
		submit_url = reverse('courses:quiz_submit', kwargs={'quiz_id': self.quiz.id})

		self.assertEqual(self.client.get(quiz_url).status_code, 404)
		self.assertEqual(self.client.post(submit_url, data='{}', content_type='application/json').status_code, 404)

		Enrollment.objects.create(user=self.student, course=self.paid_course)
		response = self.client.get(quiz_url, HTTP_ACCEPT='application/json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['quiz']['id'], self.quiz.id)

	def test_locked_lesson_is_displayed_as_not_found(self):
		self.client.force_login(self.student)

		response = self.client.get(reverse(
			'courses:lesson',
			kwargs={'course_slug': self.paid_course.slug, 'lesson_id': self.locked_lesson.id},
		))

		self.assertEqual(response.status_code, 404)
		self.assertContains(response, 'این صفحه در آکادمی پیدا نشد', status_code=404)


class ErrorPageTests(TestCase):
	def test_unknown_url_renders_custom_404_page(self):
		response = self.client.get('/this-url-does-not-exist/')

		self.assertEqual(response.status_code, 404)
		self.assertTemplateUsed(response, '404.html')
		self.assertContains(response, 'این صفحه در آکادمی پیدا نشد', status_code=404)
		self.assertContains(response, 'HTTP 404 — Not Found', status_code=404)
		self.assertContains(response, reverse('courses:home'), status_code=404)

	def test_error_handlers_are_wired_in_urlconf(self):
		from config import urls as project_urls

		self.assertEqual(project_urls.handler404, 'config.error_views.handler_404')
		self.assertEqual(project_urls.handler403, 'config.error_views.handler_403_as_404')
		self.assertEqual(project_urls.handler500, 'config.error_views.handler_500')

	def test_permission_denied_is_rendered_as_404(self):
		from config import error_views

		request = RequestFactory().get('/private/')
		request.user = AnonymousUser()
		request.session = SessionStore()

		response = error_views.handler_403_as_404(request, Exception('denied'))

		self.assertEqual(response.status_code, 404)
		self.assertIn('این صفحه در آکادمی پیدا نشد', response.content.decode())

	def test_custom_500_page_renders_without_request_context(self):
		from config import error_views

		response = error_views.handler_500(RequestFactory().get('/'))

		self.assertEqual(response.status_code, 500)
		self.assertIn('HTTP 500 — Internal Server Error', response.content.decode())
		self.assertIn('خطایی از سمت سرور رخ داد', response.content.decode())


class HomePodcastSectionTests(TestCase):
	def setUp(self):
		self.author = CustomUser.objects.create_user(
			phone_number='09120000777',
			password='test-password-123',
			full_name='حسین طاهری',
		)
		self.post = BlogPost.objects.create(
			title='اپیزود آزمایشی',
			slug='podcast-episode-test',
			content='توضیح اپیزود',
			author=self.author,
			podcast_title='برج مراقبت — قسمت اول',
			podcast_audio_url='https://example.com/episode.mp3',
			podcast_duration_minutes=8,
			published_at=timezone.make_aware(datetime(2026, 4, 6, 12, 0)),
			is_published=True,
		)

	def test_home_podcast_panel_renders_episode_from_database(self):
		response = self.client.get(reverse('courses:home'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'پادکست‌ها')
		self.assertContains(response, 'همه پادکست‌ها')
		self.assertContains(response, self.post.podcast_title)
		self.assertContains(response, 'گوینده: حسین طاهری')
		self.assertContains(response, '۱۴۰۵ فروردین ۱۷')
		self.assertContains(response, '۸:۰۰')
		self.assertContains(
			response,
			f'data-audio-target="podcast-audio-{self.post.pk}"',
		)
		self.assertContains(response, self.post.podcast_audio_url)
		self.assertContains(response, 'podcast-seek')
		self.assertContains(response, 'podcast-time-total')
		self.assertContains(response, 'data-skip="10"')
		self.assertContains(response, 'podcast-rate-up')
		self.assertContains(response, 'podcast-rate-down')


class CourseCommentTests(TestCase):
	def setUp(self):
		self.instructor = CustomUser.objects.create_user(
			phone_number='09120001001',
			password='test-password-123',
		)
		self.student = CustomUser.objects.create_user(
			phone_number='09120001002',
			password='test-password-123',
			full_name='دانشجوی نمونه',
		)
		category = Category.objects.create(name='Comments', slug='comments')
		self.course = Course.objects.create(
			title='Commented course',
			slug='commented-course',
			description='Course description',
			price=0,
			is_published=True,
			category=category,
			instructor=self.instructor,
		)
		self.comment_url = reverse('courses:comment', kwargs={'slug': self.course.slug})

	def test_ajax_comment_is_created_and_rendered_without_redirect(self):
		self.client.force_login(self.student)

		response = self.client.post(
			self.comment_url,
			{'body': 'دیدگاه آزمایشی برای این دوره'},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertEqual(data['level'], 'success')
		self.assertEqual(data['comment_count'], 1)
		self.assertIn('دیدگاه آزمایشی برای این دوره', data['html'])
		self.assertIn('دانشجوی نمونه', data['html'])
		self.assertEqual(CourseComment.objects.count(), 1)

	def test_ajax_comment_requires_login(self):
		response = self.client.post(
			self.comment_url,
			{'body': 'دیدگاه مهمان'},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 401)
		self.assertFalse(CourseComment.objects.exists())

	def test_short_comment_returns_ajax_error(self):
		self.client.force_login(self.student)

		response = self.client.post(
			self.comment_url,
			{'body': ' '},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json()['error'], 'متن دیدگاه خیلی کوتاه است.')
		self.assertFalse(CourseComment.objects.exists())

	def test_course_page_lists_only_approved_comments_and_ajax_form(self):
		CourseComment.objects.create(
			course=self.course,
			user=self.student,
			body='دیدگاه تأییدشده',
		)
		CourseComment.objects.create(
			course=self.course,
			user=self.student,
			body='دیدگاه پنهان',
			is_approved=False,
		)
		self.client.force_login(self.student)

		response = self.client.get(
			reverse('courses:detail', kwargs={'slug': self.course.slug})
		)

		self.assertContains(response, 'دیدگاه تأییدشده')
		self.assertNotContains(response, 'دیدگاه پنهان')
		self.assertContains(response, 'ajax-comment-form')
		self.assertContains(response, 'comments.js')


class CourseEditorContentTests(TestCase):
	def setUp(self):
		self.instructor = CustomUser.objects.create_user(
			phone_number='09120002001',
			password='test-password-123',
		)
		self.student = CustomUser.objects.create_user(
			phone_number='09120002002',
			password='test-password-123',
		)
		category = Category.objects.create(name='Editor', slug='editor')
		self.course = Course.objects.create(
			title='دوره با محتوای ادیتور',
			slug='editor-course',
			description='<h2>سرفصل توضیحات دوره</h2><p>متن <strong>مهم</strong> دوره.</p>',
			price=0,
			is_published=True,
			category=category,
			instructor=self.instructor,
		)
		self.chapter = Chapter.objects.create(
			course=self.course,
			title='فصل اول',
			order=1,
			description='<h3>سرتیتر فصل</h3><p>توضیح <em>فصل</em>.</p>',
		)
		self.project = FinalProject.objects.create(
			course=self.course,
			title='پروژه دوره',
			description='<h4>شرح پروژه</h4><p>متن <strong>پروژه</strong>.</p>',
		)

	def test_course_content_fields_use_ckeditor5_with_extends_config(self):
		from django_ckeditor_5.widgets import CKEditor5Widget

		for model, field_name in (
			(Course, 'description'),
			(Chapter, 'description'),
			(FinalProject, 'description'),
		):
			field = model._meta.get_field(field_name)
			widget = field.formfield().widget

			self.assertEqual(field.get_internal_type(), 'TextField')
			self.assertEqual(field.config_name, 'extends')
			self.assertIsInstance(widget, CKEditor5Widget)
			self.assertEqual(widget.config.get('language'), 'fa')
			self.assertFalse(widget._config_errors)

	def test_course_detail_renders_editor_html_safely(self):
		response = self.client.get(
			reverse('courses:detail', kwargs={'slug': self.course.slug})
		)

		self.assertContains(response, '<h2>سرفصل توضیحات دوره</h2>', html=False)
		self.assertContains(response, '<strong>مهم</strong>', html=False)
		self.assertContains(response, '<h3>سرتیتر فصل</h3>', html=False)
		self.assertNotContains(response, '&lt;h2&gt;')

	def test_chapter_and_project_pages_render_editor_html(self):
		self.client.force_login(self.student)

		chapter_response = self.client.get(reverse(
			'courses:chapter_detail',
			kwargs={'course_slug': self.course.slug, 'chapter_id': self.chapter.pk},
		))
		project_response = self.client.get(
			reverse('courses:project', kwargs={'course_slug': self.course.slug})
		)

		self.assertContains(chapter_response, '<h3>سرتیتر فصل</h3>', html=False)
		self.assertContains(chapter_response, '<em>فصل</em>', html=False)
		self.assertEqual(project_response.status_code, 200)
		self.assertContains(project_response, '<h4>شرح پروژه</h4>', html=False)
		self.assertContains(project_response, '<strong>پروژه</strong>', html=False)

	def test_rich_text_filter_handles_plain_text_and_html(self):
		from .templatetags.course_tags import rich_text

		plain = str(rich_text('خط اول\nخط دوم'))
		self.assertIn('خط اول', plain)
		self.assertIn('<br', plain)
		self.assertEqual(str(rich_text('<p>متن</p>')), '<p>متن</p>')
