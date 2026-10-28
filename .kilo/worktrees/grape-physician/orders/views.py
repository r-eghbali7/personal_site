"""Views: orders (stub)"""
from django.views import View
from django.shortcuts import render, redirect


class CartView(View):
    def get(self, request):
        return render(request, 'cart.html')


class AddToCartView(View):
    def post(self, request, course_id):
        return redirect('orders:cart')


class RemoveFromCartView(View):
    def post(self, request, item_id):
        return redirect('orders:cart')


class CheckoutView(View):
    def get(self, request):
        return render(request, 'checkout.html')


class PaymentRequestView(View):
    def post(self, request):
        return redirect('orders:cart')


class PaymentVerifyView(View):
    def get(self, request):
        return redirect('orders:payment_failed')


class PaymentSuccessView(View):
    def get(self, request):
        return render(request, 'payment_success.html')


class PaymentFailedView(View):
    def get(self, request):
        return render(request, 'payment_failed.html')
