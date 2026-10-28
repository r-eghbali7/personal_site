from django.test import TestCase
from django.urls import reverse

from courses.models import Category, Course, Enrollment
from orders.models import Order, OrderItem
from tickets.models import Ticket, TicketMessage
from .models import CustomUser, OTPCode


class AccountFlowTests(TestCase):
	def test_otp_page_has_six_inputs_and_accepts_valid_code(self):
		phone = '09123456789'
		otp = OTPCode.create_for_phone(phone)
		session = self.client.session
		session['register_data'] = {
			'phone_number': phone,
			'full_name': 'Test User',
			'password': 'secure-pass-123',
			'action': 'register',
		}
		session.save()

		response = self.client.get(reverse('accounts:otp_verify'))
		self.assertEqual(response.content.count(b'class="otp-input'), 6)
		response = self.client.post(
			reverse('accounts:otp_verify'),
			{'code': otp.code},
		)

		self.assertRedirects(response, reverse('courses:home'))
		self.assertTrue(CustomUser.objects.filter(phone_number=phone).exists())
		otp.refresh_from_db()
		self.assertTrue(otp.is_used)

	def test_login_preserves_safe_next_and_rejects_external_next(self):
		user = CustomUser.objects.create_user(
			phone_number='09123456789',
			password='secure-pass-123',
		)
		login_url = reverse('accounts:login')

		response = self.client.post(
			login_url,
			{'mobile': user.phone_number, 'password': 'secure-pass-123', 'next': '/accounts/profile/'},
		)
		self.assertRedirects(response, '/accounts/profile/')

		self.client.logout()
		response = self.client.post(
			login_url,
			{'mobile': user.phone_number, 'password': 'secure-pass-123', 'next': 'https://example.com/'},
		)
		self.assertRedirects(response, reverse('courses:home'))

	def test_profile_update_and_logout_use_server_endpoints(self):
		user = CustomUser.objects.create_user(
			phone_number='09123456789',
			password='secure-pass-123',
		)
		self.client.force_login(user)

		response = self.client.post(
			reverse('accounts:profile'),
			{'full_name': 'Updated Name', 'email': 'updated@example.com', 'bio': 'Updated bio'},
		)
		self.assertRedirects(response, reverse('accounts:profile'))
		user.refresh_from_db()
		self.assertEqual(user.full_name, 'Updated Name')
		self.assertEqual(user.email, 'updated@example.com')
		self.assertEqual(user.bio, 'Updated bio')

		response = self.client.post(reverse('accounts:logout'))
		self.assertRedirects(response, reverse('courses:home'))
		self.assertNotIn('_auth_user_id', self.client.session)

	def test_profile_page_renders_for_authenticated_user(self):
		user = CustomUser.objects.create_user(
			phone_number='09123456789',
			password='secure-pass-123',
			full_name='Profile User',
		)
		self.client.force_login(user)

		response = self.client.get(reverse('accounts:profile'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Profile User')

	def test_profile_dashboard_shows_only_current_users_database_records(self):
		user = CustomUser.objects.create_user(
			phone_number='09123330001',
			password='secure-pass-123',
			full_name='Current Student',
		)
		other_user = CustomUser.objects.create_user(
			phone_number='09123330002',
			password='secure-pass-123',
			full_name='Other Student',
		)
		category = Category.objects.create(name='Profile courses', slug='profile-courses')
		own_course = Course.objects.create(
			title='My enrolled course',
			slug='my-enrolled-course',
			description='Course details',
			is_published=True,
			category=category,
			instructor=user,
		)
		other_course = Course.objects.create(
			title='Private other course',
			slug='private-other-course',
			description='Other course details',
			is_published=True,
			category=category,
			instructor=other_user,
		)
		Enrollment.objects.create(user=user, course=own_course)
		Enrollment.objects.create(user=other_user, course=other_course)
		order = Order.objects.create(user=user, total_amount=2500, status='paid')
		OrderItem.objects.create(order=order, course=own_course, price=2500)
		Ticket.objects.create(user=user, subject='My profile ticket', course=own_course)
		Ticket.objects.create(user=other_user, subject='Other private ticket', course=other_course)
		self.client.force_login(user)

		response = self.client.get(reverse('accounts:profile'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Current Student')
		self.assertContains(response, own_course.title)
		self.assertContains(response, 'My profile ticket')
		self.assertEqual(response.context['enrollment_count'], 1)
		self.assertEqual(response.context['order_count'], 1)
		self.assertEqual(response.context['ticket_count'], 1)
		self.assertNotContains(response, other_course.title)
		self.assertNotContains(response, 'Other private ticket')
		self.assertNotContains(response, 'مهندس آرش سرمدی')
		self.assertNotContains(response, '۷۸٪')

	def test_profile_ticket_creation_is_saved_for_current_user_and_owned_course(self):
		user = CustomUser.objects.create_user(
			phone_number='09123330003',
			password='secure-pass-123',
		)
		other_user = CustomUser.objects.create_user(
			phone_number='09123330004',
			password='secure-pass-123',
		)
		category = Category.objects.create(name='Ticket courses', slug='ticket-courses')
		own_course = Course.objects.create(
			title='Enrolled course', slug='enrolled-course', description='Details',
			is_published=True, category=category, instructor=user,
		)
		other_course = Course.objects.create(
			title='Not enrolled course', slug='not-enrolled-course', description='Details',
			is_published=True, category=category, instructor=other_user,
		)
		Enrollment.objects.create(user=user, course=own_course)
		self.client.force_login(user)
		profile_url = reverse('accounts:profile')

		response = self.client.post(profile_url, {
			'action': 'create_ticket',
			'subject': 'Question about my course',
			'body': 'Please help me with this lesson.',
			'course': str(own_course.pk),
		})

		self.assertRedirects(response, f'{profile_url}#tab-tickets')
		ticket = Ticket.objects.get(subject='Question about my course')
		self.assertEqual(ticket.user, user)
		self.assertEqual(ticket.course, own_course)
		self.assertEqual(ticket.messages.get().sender, user)

		invalid_response = self.client.post(profile_url, {
			'action': 'create_ticket',
			'subject': 'Trying another course',
			'body': 'This course is not enrolled for me.',
			'course': str(other_course.pk),
		})
		self.assertEqual(invalid_response.status_code, 400)
		self.assertFalse(Ticket.objects.filter(subject='Trying another course').exists())

	def test_password_change_validates_and_keeps_user_logged_in(self):
		user = CustomUser.objects.create_user(
			phone_number='09123456789',
			password='secure-pass-123',
		)
		self.client.force_login(user)

		response = self.client.post(reverse('accounts:password_change'), {
			'old_password': 'secure-pass-123',
			'new_password1': 'AnotherSecurePass-987',
			'new_password2': 'AnotherSecurePass-987',
		})

		self.assertRedirects(response, f"{reverse('accounts:profile')}#tab-security")
		user.refresh_from_db()
		self.assertTrue(user.check_password('AnotherSecurePass-987'))
		self.assertTrue(response.wsgi_request.user.is_authenticated)

	def test_registration_rejects_weak_password(self):
		response = self.client.post(reverse('accounts:register'), {
			'fullname': 'Test User',
			'mobile': '09123456789',
			'password': 'password',
		})

		self.assertEqual(response.status_code, 200)
		self.assertFalse(OTPCode.objects.exists())
		self.assertContains(response, 'رمز عبور')
