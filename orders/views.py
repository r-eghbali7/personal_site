"""Views: cart and payment workflows."""
from decimal import Decimal

import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction as db_transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from courses.models import Course, Enrollment
from .models import Cart, CartItem, Coupon, CouponRedemption, Order, OrderItem, Transaction


def get_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def safe_next_url(request):
    """آدرس بازگشت معتبر (همان دامنه) را برمی‌گرداند؛ در غیر این صورت خالی."""
    next_url = request.POST.get('next') or ''
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return ''


def cart_summary(cart, user):
    """مبالغ سبد خرید به‌همراه وضعیت کد تخفیف اعمال‌شده."""
    subtotal = cart.get_subtotal()
    coupon = cart.coupon if cart.coupon_id else None
    discount = Decimal('0')
    coupon_error = ''
    if coupon is not None:
        value, coupon_error = coupon.validate_for_cart(cart, user)
        discount = value or Decimal('0')
    return {
        'subtotal': subtotal,
        'discount': discount,
        'payable': max(subtotal - discount, Decimal('0')),
        'coupon': coupon,
        'coupon_error': coupon_error,
    }


def redeem_coupon(order):
    """ثبت استفاده موفق از کد تخفیف و افزایش شمارنده استفاده."""
    if not order.coupon_id or order.discount_amount <= 0:
        return
    redemption, created = CouponRedemption.objects.get_or_create(
        coupon_id=order.coupon_id,
        order=order,
        defaults={'user': order.user, 'discount_amount': order.discount_amount},
    )
    if created:
        Coupon.objects.filter(pk=order.coupon_id).update(used_count=F('used_count') + 1)


def complete_paid_order(order):
    """پایان موفق سفارش: ثبت‌نام دوره‌ها، پاک کردن سبد و مصرف کد تخفیف."""
    with db_transaction.atomic():
        order.status = 'paid'
        order.save(update_fields=['status', 'updated_at'])
        for item in order.items.select_related('course'):
            Enrollment.objects.update_or_create(
                user=order.user,
                course=item.course,
                defaults={'is_active': True},
            )
            CartItem.objects.filter(cart__user=order.user, course=item.course).delete()
        Cart.objects.filter(user=order.user).update(coupon=None)
        redeem_coupon(order)


class CartView(View):
    def get(self, request):
        cart = get_cart(request)
        return render(request, 'cart.html', {
            'cart': cart,
            'items': cart.items.select_related('course'),
            **cart_summary(cart, request.user),
        })


class ApplyCouponView(View):
    def post(self, request):
        code = (request.POST.get('code') or '').strip()
        next_url = safe_next_url(request) or reverse('orders:cart')
        cart = get_cart(request)
        if not code:
            messages.error(request, 'لطفاً کد تخفیف را وارد کنید.')
            return redirect(next_url)
        coupon = Coupon.objects.filter(code__iexact=code).first()
        if coupon is None:
            messages.error(request, 'کد تخفیف وارد‌شده معتبر نیست.')
            return redirect(next_url)
        discount, error = coupon.validate_for_cart(cart, request.user)
        if error:
            messages.error(request, error)
            return redirect(next_url)
        cart.coupon = coupon
        cart.save(update_fields=['coupon'])
        messages.success(
            request,
            f'کد تخفیف «{coupon.code}» اعمال شد و {discount:,.0f} تومان از مبلغ سبد کم شد.',
        )
        return redirect(next_url)


class RemoveCouponView(View):
    def post(self, request):
        cart = get_cart(request)
        if cart.coupon_id:
            cart.coupon = None
            cart.save(update_fields=['coupon'])
            messages.error(request, 'کد تخفیف از سبد خرید حذف شد.')
        return redirect(safe_next_url(request) or reverse('orders:cart'))


class AddToCartView(View):
    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id, is_published=True)
        if course.is_free:
            if not request.user.is_authenticated:
                return redirect(f"{reverse('accounts:login')}?next={request.path}")
            Enrollment.objects.get_or_create(user=request.user, course=course)
            messages.success(request, 'ثبت‌نام دوره رایگان با موفقیت انجام شد.')
            return redirect('courses:detail', slug=course.slug)
        if course.is_enrolled(request.user):
            messages.info(request, 'این دوره رایگان است یا قبلاً به آن دسترسی دارید.')
            return redirect('courses:detail', slug=course.slug)
        cart = get_cart(request)
        CartItem.objects.get_or_create(
            cart=cart,
            course=course,
            defaults={'price_snapshot': course.price},
        )
        messages.success(request, 'دوره به سبد خرید اضافه شد.')
        return redirect('orders:cart')


class RemoveFromCartView(View):
    def post(self, request, item_id):
        cart = get_cart(request)
        get_object_or_404(CartItem, pk=item_id, cart=cart).delete()
        messages.error(request, 'دوره از سبد خرید حذف شد.')
        if cart.coupon_id:
            _discount, error = cart.coupon.validate_for_cart(cart, request.user)
            if error:
                cart.coupon = None
                cart.save(update_fields=['coupon'])
                messages.warning(request, 'با حذف این دوره، کد تخفیف از سبد خرید برداشته شد.')
        return redirect('orders:cart')


class CheckoutView(LoginRequiredMixin, View):
    def get(self, request):
        cart = get_cart(request)
        items = cart.items.select_related('course')
        if not items.exists():
            messages.info(request, 'سبد خرید شما خالی است.')
            return redirect('orders:cart')
        return render(request, 'checkout.html', {
            'items': items,
            **cart_summary(cart, request.user),
        })


class PaymentRequestView(LoginRequiredMixin, View):
    def post(self, request):
        cart = get_cart(request)
        items = list(cart.items.select_related('course'))
        if not items:
            messages.error(request, 'سبد خرید شما خالی است.')
            return redirect('orders:cart')

        subtotal = sum((item.course.price for item in items), Decimal('0'))
        coupon = cart.coupon if cart.coupon_id else None
        discount = Decimal('0')
        if coupon is not None:
            discount_value, error = coupon.validate_for_cart(cart, request.user)
            if error:
                cart.coupon = None
                cart.save(update_fields=['coupon'])
                messages.error(request, error)
                return redirect('orders:cart')
            discount = discount_value
        payable = max(subtotal - discount, Decimal('0'))

        if payable <= 0:
            order = Order.objects.create(
                user=request.user,
                coupon=coupon,
                subtotal_amount=subtotal,
                discount_amount=discount,
                total_amount=payable,
            )
            OrderItem.objects.bulk_create([
                OrderItem(order=order, course=item.course, price=item.course.price)
                for item in items
            ])
            complete_paid_order(order)
            messages.success(
                request,
                'با کد تخفیف اعمال‌شده مبلغ قابل پرداخت صفر شد و ثبت‌نام شما تکمیل شد.',
            )
            return redirect('orders:payment_success')

        merchant_id = getattr(settings, 'ZARINPAL_MERCHANT_ID', '')
        if not merchant_id or merchant_id.startswith('YOUR_'):
            messages.error(request, 'درگاه پرداخت هنوز پیکربندی نشده است.')
            return redirect('orders:checkout')

        order = Order.objects.create(
            user=request.user,
            coupon=coupon,
            subtotal_amount=subtotal,
            discount_amount=discount,
            total_amount=payable,
        )
        OrderItem.objects.bulk_create([
            OrderItem(order=order, course=item.course, price=item.course.price)
            for item in items
        ])
        callback_url = request.build_absolute_uri(reverse('orders:payment_verify'))
        sandbox = getattr(settings, 'ZARINPAL_SANDBOX', True)
        api_base = 'https://sandbox.zarinpal.com/pg/v4' if sandbox else 'https://payment.zarinpal.com/pg/v4'
        try:
            response = requests.post(
                f'{api_base}/payment/request.json',
                json={
                    'merchant_id': merchant_id,
                    'amount': int(payable * 10),
                    'callback_url': callback_url,
                    'description': f'پرداخت سفارش #{order.pk}',
                    'metadata': {'mobile': request.user.phone_number},
                },
                timeout=10,
            )
            payload = response.json()
            payment_data = payload.get('data', {}) if isinstance(payload, dict) else {}
            if not isinstance(payment_data, dict):
                payment_data = {}
            authority = payment_data.get('authority')
            if response.ok and payment_data.get('code') == 100 and authority:
                Transaction.objects.create(
                    order=order,
                    authority=authority,
                    amount=int(payable * 10),
                )
                gateway = 'https://sandbox.zarinpal.com/pg/StartPay' if sandbox else 'https://www.zarinpal.com/pg/StartPay'
                return redirect(f'{gateway}/{authority}')
        except (requests.RequestException, ValueError):
            pass

        order.status = 'failed'
        order.save(update_fields=['status', 'updated_at'])
        messages.error(request, 'ارتباط با درگاه پرداخت برقرار نشد. دوباره تلاش کنید.')
        return redirect('orders:checkout')


class PaymentVerifyView(View):
    def get(self, request):
        authority = request.GET.get('Authority', '')
        transaction_record = Transaction.objects.select_related('order').filter(
            authority=authority,
        ).first()
        if not transaction_record:
            return redirect('orders:payment_failed')
        if transaction_record.status == 'success':
            return redirect('orders:payment_success')
        if request.GET.get('Status') != 'OK':
            transaction_record.status = 'failed'
            transaction_record.save(update_fields=['status', 'updated_at'])
            transaction_record.order.status = 'failed'
            transaction_record.order.save(update_fields=['status', 'updated_at'])
            return redirect('orders:payment_failed')

        sandbox = getattr(settings, 'ZARINPAL_SANDBOX', True)
        api_base = 'https://sandbox.zarinpal.com/pg/v4' if sandbox else 'https://payment.zarinpal.com/pg/v4'
        try:
            response = requests.post(
                f'{api_base}/payment/verify.json',
                json={
                    'merchant_id': settings.ZARINPAL_MERCHANT_ID,
                    'amount': int(transaction_record.amount),
                    'authority': authority,
                },
                timeout=10,
            )
            payload = response.json()
            payment_data = payload.get('data', {}) if isinstance(payload, dict) else {}
            if not isinstance(payment_data, dict):
                payment_data = {}
        except (requests.RequestException, ValueError):
            return redirect('orders:payment_failed')

        if not response.ok or payment_data.get('code') not in (100, 101):
            transaction_record.status = 'failed'
            transaction_record.save(update_fields=['status', 'updated_at'])
            transaction_record.order.status = 'failed'
            transaction_record.order.save(update_fields=['status', 'updated_at'])
            return redirect('orders:payment_failed')

        with db_transaction.atomic():
            transaction_record.status = 'success'
            transaction_record.ref_id = str(payment_data.get('ref_id', ''))
            transaction_record.save(update_fields=['status', 'ref_id', 'updated_at'])
            complete_paid_order(transaction_record.order)
        return redirect('orders:payment_success')


class PaymentSuccessView(View):
    def get(self, request):
        return render(request, 'payment_success.html')


class PaymentFailedView(View):
    def get(self, request):
        return render(request, 'payment_failed.html')
