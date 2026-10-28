from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from .models import Category, Chapter, Course, Enrollment, Lesson, Quiz


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

		self.assertEqual(self.client.get(quiz_url).status_code, 403)
		self.assertEqual(self.client.post(submit_url, data='{}', content_type='application/json').status_code, 403)

		Enrollment.objects.create(user=self.student, course=self.paid_course)
		response = self.client.get(quiz_url, HTTP_ACCEPT='application/json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['quiz']['id'], self.quiz.id)
