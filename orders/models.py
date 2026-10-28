"""
App: orders — مدل‌های سبد خرید، سفارش و تراکنش زرین‌پال
"""

from django.db import models
from django.conf import settings


class Cart(models.Model):
    """
    سبد خرید.
    - برای کاربران لاگین‌شده: user پر می‌شود
    - برای مهمان: session_key پر می‌شود
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart',
        verbose_name='کاربر',
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        verbose_name='کلید سشن (مهمان)',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'سبد خرید'
        verbose_name_plural = 'سبدهای خرید'

    def __str__(self):
        return f'Cart({self.user or self.session_key})'

    def get_total(self):
        return sum(item.price_snapshot for item in self.items.all())

    def get_items_count(self):
        return self.items.count()


class CartItem(models.Model):
    """آیتم داخل سبد خرید."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='سبد خرید',
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='دوره',
    )
    price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='قیمت در لحظه افزودن',
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ افزودن')

    class Meta:
        verbose_name = 'آیتم سبد'
        verbose_name_plural = 'آیتم‌های سبد'
        unique_together = ('cart', 'course')

    def __str__(self):
        return f'{self.course.title} در سبد {self.cart}'


class Order(models.Model):
    """سفارش نهایی پس از تأیید سبد خرید."""

    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('failed', 'ناموفق'),
        ('refunded', 'برگشت وجه'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='کاربر',
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='مبلغ کل (تومان)',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.pk} — {self.user} — {self.get_status_display()}'


class OrderItem(models.Model):
    """آیتم‌های یک سفارش (snapshot از سبد خرید)."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='سفارش',
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='دوره',
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='قیمت خرید',
    )

    class Meta:
        verbose_name = 'آیتم سفارش'
        verbose_name_plural = 'آیتم‌های سفارش'

    def __str__(self):
        return f'{self.course.title} — سفارش #{self.order.pk}'


class Transaction(models.Model):
    """لاگ تراکنش‌های زرین‌پال."""

    STATUS_CHOICES = [
        ('initiated', 'شروع شده'),
        ('success', 'موفق'),
        ('failed', 'ناموفق'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='سفارش',
    )
    authority = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='کد authority زرین‌پال',
    )
    ref_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='کد رهگیری نهایی',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated',
        verbose_name='وضعیت',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='مبلغ (ریال)',
        help_text='زرین‌پال با ریال کار می‌کند.',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f'TX #{self.pk} — {self.authority[:20]}... — {self.get_status_display()}'
