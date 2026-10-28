from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomUser
from courses.models import Category, Course
from .models import Cart, CartItem


class CartFlowTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			phone_number='09125556666',
			password='test-password-123',
		)
		instructor = CustomUser.objects.create_user(
			phone_number='09127778888',
			password='test-password-123',
		)
		category = Category.objects.create(name='Testing', slug='testing')
		self.course = Course.objects.create(
			title='Django Testing',
			slug='django-testing',
			description='Test course',
			price=125000,
			is_published=True,
			category=category,
			instructor=instructor,
		)

	def test_guest_can_add_remove_cart_item_without_changing_course_price(self):
		add_url = reverse('orders:add_to_cart', kwargs={'course_id': self.course.pk})
		response = self.client.post(add_url)
		self.assertRedirects(response, reverse('orders:cart'))
		item = CartItem.objects.get(course=self.course)
		self.assertEqual(item.price_snapshot, self.course.price)

		self.client.post(reverse('orders:add_to_cart', kwargs={'course_id': self.course.pk}))
		self.assertEqual(CartItem.objects.filter(cart=item.cart).count(), 1)

		response = self.client.get(reverse('orders:cart'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Django Testing')

		self.client.post(reverse('orders:remove_from_cart', kwargs={'item_id': item.pk}))
		self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

	def test_free_course_enrollment_is_persisted_for_authenticated_user(self):
		free_course = Course.objects.create(
			title='Free course',
			slug='free-course',
			description='Free course description',
			price=0,
			is_published=True,
			instructor=self.course.instructor,
		)
		self.client.force_login(self.user)

		response = self.client.post(reverse('orders:add_to_cart', kwargs={'course_id': free_course.pk}))

		self.assertRedirects(response, reverse('courses:detail', kwargs={'slug': free_course.slug}))
		self.assertTrue(free_course.is_enrolled(self.user))

	@override_settings(ZARINPAL_MERCHANT_ID='YOUR_ZARINPAL_MERCHANT_ID_HERE')
	def test_payment_requires_login_and_missing_gateway_configuration(self):
		cart = Cart.objects.create(user=self.user)
		CartItem.objects.create(cart=cart, course=self.course, price_snapshot=self.course.price)
		request_url = reverse('orders:payment_request')

		response = self.client.post(request_url)
		self.assertRedirects(response, f"{reverse('accounts:login')}?next={request_url}")

		self.client.force_login(self.user)
		response = self.client.post(request_url)
		self.assertRedirects(response, reverse('orders:checkout'))
		self.assertFalse(self.user.orders.exists())
