"""Views: cart and payment workflows."""
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from courses.models import Course, Enrollment
from .models import Cart, CartItem, Order, OrderItem, Transaction


def get_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


class CartView(View):
    def get(self, request):
        cart = get_cart(request)
        return render(request, 'cart.html', {
            'cart': cart,
            'items': cart.items.select_related('course'),
            'total': cart.get_total(),
        })


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
        get_object_or_404(CartItem, pk=item_id, cart=get_cart(request)).delete()
        return redirect('orders:cart')


class CheckoutView(LoginRequiredMixin, View):
    def get(self, request):
        cart = get_cart(request)
        items = cart.items.select_related('course')
        if not items.exists():
            messages.info(request, 'سبد خرید شما خالی است.')
            return redirect('orders:cart')
        return render(request, 'checkout.html', {'items': items, 'total': cart.get_total()})


class PaymentRequestView(LoginRequiredMixin, View):
    def post(self, request):
        cart = get_cart(request)
        items = list(cart.items.select_related('course'))
        if not items:
            messages.error(request, 'سبد خرید شما خالی است.')
            return redirect('orders:cart')

        total_toman = sum(item.course.price for item in items)
        if total_toman <= 0:
            messages.error(request, 'مبلغ سفارش معتبر نیست.')
            return redirect('orders:cart')

        merchant_id = getattr(settings, 'ZARINPAL_MERCHANT_ID', '')
        if not merchant_id or merchant_id.startswith('YOUR_'):
            messages.error(request, 'درگاه پرداخت هنوز پیکربندی نشده است.')
            return redirect('orders:checkout')

        order = Order.objects.create(user=request.user, total_amount=total_toman)
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
                    'amount': int(total_toman * 10),
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
                    amount=int(total_toman * 10),
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
            order = transaction_record.order
            order.status = 'paid'
            order.save(update_fields=['status', 'updated_at'])
            for item in order.items.select_related('course'):
                Enrollment.objects.update_or_create(
                    user=order.user,
                    course=item.course,
                    defaults={'is_active': True},
                )
                CartItem.objects.filter(cart__user=order.user, course=item.course).delete()
        return redirect('orders:payment_success')


class PaymentSuccessView(View):
    def get(self, request):
        return render(request, 'payment_success.html')


class PaymentFailedView(View):
    def get(self, request):
        return render(request, 'payment_failed.html')
