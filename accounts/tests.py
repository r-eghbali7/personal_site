from django.test import TestCase
from django.urls import reverse

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
