from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser
from courses.models import Category, Course
from .models import (
    Cart,
    CartItem,
    Coupon,
    CouponRedemption,
    Order,
    OrderItem,
    Transaction,
)


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


class CouponTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            phone_number='09121110000',
            password='test-password-123',
        )
        self.other_user = CustomUser.objects.create_user(
            phone_number='09121110001',
            password='test-password-123',
        )
        instructor = CustomUser.objects.create_user(
            phone_number='09121110002',
            password='test-password-123',
        )
        category = Category.objects.create(name='Coupon tests', slug='coupon-tests')
        self.course = Course.objects.create(
            title='Course A',
            slug='course-a',
            description='Description A',
            price=100000,
            is_published=True,
            category=category,
            instructor=instructor,
        )
        self.course2 = Course.objects.create(
            title='Course B',
            slug='course-b',
            description='Description B',
            price=50000,
            is_published=True,
            category=category,
            instructor=instructor,
        )
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=self.cart,
            course=self.course,
            price_snapshot=self.course.price,
        )

    def make_coupon(self, **overrides):
        data = {
            'code': 'TEST10',
            'discount_type': Coupon.PERCENT,
            'value': Decimal('10'),
            'per_user_limit': 1,
        }
        data.update(overrides)
        return Coupon.objects.create(**data)

    def test_user_specific_coupon_only_for_that_user_and_inside_window(self):
        now = timezone.now()
        coupon = self.make_coupon(
            code='VIP10',
            user=self.user,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=1),
        )

        discount, error = coupon.validate_for_cart(self.cart, self.user)
        self.assertEqual(error, '')
        self.assertEqual(discount, Decimal('10000'))

        other_cart = Cart.objects.create(user=self.other_user)
        CartItem.objects.create(
            cart=other_cart,
            course=self.course,
            price_snapshot=self.course.price,
        )
        discount, error = coupon.validate_for_cart(other_cart, self.other_user)
        self.assertIsNone(discount)
        self.assertIn('کاربر مشخصی', error)

        self.assertIn('هنوز شروع نشده', coupon.active_error(now - timedelta(days=2)))
        self.assertIn('به پایان رسیده', coupon.active_error(now + timedelta(days=2)))

    def test_public_coupon_for_one_course_requires_that_course_in_cart(self):
        coupon = self.make_coupon(
            code='COURSE20',
            value=Decimal('20'),
            course=self.course2,
            valid_until=timezone.now() + timedelta(days=7),
        )

        discount, error = coupon.validate_for_cart(self.cart, self.user)
        self.assertIsNone(discount)
        self.assertIn('فقط برای دوره', error)

        CartItem.objects.create(
            cart=self.cart,
            course=self.course2,
            price_snapshot=self.course2.price,
        )
        discount, error = coupon.validate_for_cart(self.cart, self.user)
        self.assertEqual(error, '')
        self.assertEqual(discount, Decimal('10000'))

    def test_global_coupon_applies_to_all_products(self):
        percent_coupon = self.make_coupon(code='ALL15', value=Decimal('15'))
        discount, error = percent_coupon.validate_for_cart(self.cart, self.user)
        self.assertEqual(error, '')
        self.assertEqual(discount, Decimal('15000'))

        fixed_coupon = self.make_coupon(
            code='ALL25K',
            discount_type=Coupon.FIXED,
            value=Decimal('25000'),
        )
        discount, error = fixed_coupon.validate_for_cart(self.cart, self.user)
        self.assertEqual(error, '')
        self.assertEqual(discount, Decimal('25000'))

    def test_time_limited_global_coupon_is_rejected_after_expiry(self):
        coupon = self.make_coupon(
            code='EXPIRED',
            valid_from=timezone.now() - timedelta(days=2),
            valid_until=timezone.now() - timedelta(minutes=1),
        )
        discount, error = coupon.validate_for_cart(self.cart, self.user)
        self.assertIsNone(discount)
        self.assertIn('به پایان رسیده', error)

        coupon.valid_until = timezone.now() + timedelta(days=1)
        coupon.save(update_fields=['valid_until'])
        discount, error = coupon.validate_for_cart(self.cart, self.user)
        self.assertEqual(error, '')
        self.assertEqual(discount, Decimal('10000'))

    def test_inactive_and_exhausted_coupons_are_rejected(self):
        inactive = self.make_coupon(code='OFF', is_active=False)
        discount, error = inactive.validate_for_cart(self.cart, self.user)
        self.assertIsNone(discount)
        self.assertIn('غیرفعال', error)

        exhausted = self.make_coupon(code='FULL', usage_limit=1, used_count=1)
        discount, error = exhausted.validate_for_cart(self.cart, self.user)
        self.assertIsNone(discount)
        self.assertIn('ظرفیت', error)

    def test_per_user_limit_counts_previous_redemptions(self):
        coupon = self.make_coupon(code='ONCE', per_user_limit=1)
        order = Order.objects.create(
            user=self.user,
            coupon=coupon,
            subtotal_amount=Decimal('100000'),
            discount_amount=Decimal('10000'),
            total_amount=Decimal('90000'),
        )
        CouponRedemption.objects.create(
            coupon=coupon,
            user=self.user,
            order=order,
            discount_amount=Decimal('10000'),
        )

        discount, error = coupon.validate_for_cart(self.cart, self.user)
        self.assertIsNone(discount)
        self.assertIn('قبلاً', error)

    def test_apply_and_remove_coupon_through_cart_endpoints(self):
        self.make_coupon(code='apply10')
        self.client.force_login(self.user)

        response = self.client.post(reverse('orders:apply_coupon'), {'code': 'apply10'})
        self.assertRedirects(response, reverse('orders:cart'))
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.coupon.code, 'APPLY10')

        page = self.client.get(reverse('orders:cart'))
        self.assertContains(page, 'APPLY10')
        self.assertContains(page, 'مبلغ قابل پرداخت')

        response = self.client.post(reverse('orders:remove_coupon'))
        self.assertRedirects(response, reverse('orders:cart'))
        self.cart.refresh_from_db()
        self.assertIsNone(self.cart.coupon)

    def test_checkout_page_shows_applied_coupon(self):
        coupon = self.make_coupon(code='CHK10')
        self.cart.coupon = coupon
        self.cart.save(update_fields=['coupon'])
        self.client.force_login(self.user)

        response = self.client.get(reverse('orders:checkout'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CHK10')
        self.assertContains(response, 'مبلغ قابل پرداخت')

    def test_course_detail_page_has_working_coupon_form(self):
        response = self.client.get(
            reverse('courses:detail', kwargs={'slug': self.course.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('orders:apply_coupon'))

    def test_apply_from_checkout_redirects_back_and_ignores_external_next(self):
        self.make_coupon(code='CHKNEXT')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('orders:apply_coupon'),
            {'code': 'CHKNEXT', 'next': reverse('orders:checkout')},
        )
        self.assertRedirects(response, reverse('orders:checkout'))

        response = self.client.post(
            reverse('orders:apply_coupon'),
            {'code': 'CHKNEXT', 'next': 'https://evil.example.com/'},
        )
        self.assertRedirects(response, reverse('orders:cart'))

    def test_invalid_or_unrelated_coupon_code_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('orders:apply_coupon'), {'code': 'DOES-NOT-EXIST'}, follow=True,
        )
        self.assertContains(response, 'معتبر نیست')
        self.cart.refresh_from_db()
        self.assertIsNone(self.cart.coupon)

        self.make_coupon(code='OTHERUSER', user=self.other_user)
        response = self.client.post(
            reverse('orders:apply_coupon'), {'code': 'OTHERUSER'}, follow=True,
        )
        self.assertContains(response, 'کاربر مشخصی')
        self.cart.refresh_from_db()
        self.assertIsNone(self.cart.coupon)

    def test_removing_the_coupon_course_clears_the_coupon(self):
        coupon = self.make_coupon(code='ONLYB', course=self.course2)
        item = CartItem.objects.create(
            cart=self.cart,
            course=self.course2,
            price_snapshot=self.course2.price,
        )
        self.cart.coupon = coupon
        self.cart.save(update_fields=['coupon'])
        self.client.force_login(self.user)

        self.client.post(reverse('orders:remove_from_cart', kwargs={'item_id': item.pk}))

        self.cart.refresh_from_db()
        self.assertIsNone(self.cart.coupon)

    @override_settings(ZARINPAL_MERCHANT_ID='YOUR_ZARINPAL_MERCHANT_ID_HERE')
    def test_coupon_order_still_requires_gateway_configuration(self):
        coupon = self.make_coupon(code='PAY10')
        self.cart.coupon = coupon
        self.cart.save(update_fields=['coupon'])
        self.client.force_login(self.user)

        response = self.client.post(reverse('orders:payment_request'))

        self.assertRedirects(response, reverse('orders:checkout'))
        self.assertFalse(Order.objects.filter(user=self.user).exists())

    def test_full_discount_order_completes_without_gateway(self):
        coupon = self.make_coupon(code='FREE100', value=Decimal('100'))
        self.cart.coupon = coupon
        self.cart.save(update_fields=['coupon'])
        self.client.force_login(self.user)

        response = self.client.post(reverse('orders:payment_request'))

        self.assertRedirects(response, reverse('orders:payment_success'))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.status, 'paid')
        self.assertEqual(order.total_amount, Decimal('0'))
        self.assertEqual(order.discount_amount, Decimal('100000'))
        self.assertTrue(self.course.is_enrolled(self.user))
        coupon.refresh_from_db()
        self.assertEqual(coupon.used_count, 1)
        self.assertFalse(CartItem.objects.filter(cart=self.cart).exists())

    def test_successful_payment_redeems_coupon_only_once(self):
        coupon = self.make_coupon(code='PAY10')
        order = Order.objects.create(
            user=self.user,
            coupon=coupon,
            subtotal_amount=Decimal('100000'),
            discount_amount=Decimal('10000'),
            total_amount=Decimal('90000'),
        )
        OrderItem.objects.create(order=order, course=self.course, price=Decimal('100000'))
        Transaction.objects.create(order=order, authority='AUTH-COUPON-1', amount=900000)

        with mock.patch('orders.views.requests.post') as post:
            post.return_value.ok = True
            post.return_value.json.return_value = {'data': {'code': 100, 'ref_id': 'REF-1'}}
            response = self.client.get(
                reverse('orders:payment_verify'),
                {'Authority': 'AUTH-COUPON-1', 'Status': 'OK'},
            )

        self.assertRedirects(response, reverse('orders:payment_success'))
        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        coupon.refresh_from_db()
        self.assertEqual(coupon.used_count, 1)
        self.assertEqual(CouponRedemption.objects.filter(coupon=coupon).count(), 1)
        self.assertTrue(self.course.is_enrolled(self.user))

        with mock.patch('orders.views.requests.post') as second_post:
            self.client.get(
                reverse('orders:payment_verify'),
                {'Authority': 'AUTH-COUPON-1', 'Status': 'OK'},
            )
            second_post.assert_not_called()
        coupon.refresh_from_db()
        self.assertEqual(coupon.used_count, 1)


class CouponAdminTests(TestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            phone_number='09120000099',
            password='admin-password-123',
        )
        self.client.force_login(self.admin_user)

    def test_coupon_admin_pages_render(self):
        add_page = self.client.get(reverse('admin:orders_coupon_add'))
        self.assertEqual(add_page.status_code, 200)
        self.assertContains(add_page, 'محدوده استفاده')

        coupon = Coupon.objects.create(code='ADMIN10', value=Decimal('10'))
        changelist = self.client.get(reverse('admin:orders_coupon_changelist'))
        self.assertEqual(changelist.status_code, 200)
        change_page = self.client.get(
            reverse('admin:orders_coupon_change', args=[coupon.pk])
        )
        self.assertEqual(change_page.status_code, 200)
        self.assertContains(change_page, 'آمار استفاده')
