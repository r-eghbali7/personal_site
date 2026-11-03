"""
App: orders — مدل‌های سبد خرید، سفارش و تراکنش زرین‌پال
"""

from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


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
        db_index=True,
        verbose_name='کلید سشن (مهمان)',
    )
    coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts',
        verbose_name='کد تخفیف اعمال‌شده',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'سبد خرید'
        verbose_name_plural = 'سبدهای خرید'

    def __str__(self):
        return f'Cart({self.user or self.session_key})'

    def get_subtotal(self):
        """جمع قیمت جاری دوره‌های سبد پیش از تخفیف."""
        total = sum(
            (item.course.price for item in self.items.select_related('course')),
            Decimal('0'),
        )
        return Decimal(total)

    def get_total(self):
        """مبلغ سبد پیش از تخفیف (قیمت لحظه افزودن فقط برای سابقه نگه داشته می‌شود)."""
        return self.get_subtotal()

    def coupon_discount(self, user=None):
        """مبلغ تخفیف کد اعمال‌شده برای شرایط فعلی سبد و کاربر."""
        if not self.coupon_id:
            return Decimal('0')
        discount, _error = self.coupon.validate_for_cart(self, user)
        return discount or Decimal('0')

    def get_payable_total(self, user=None):
        """مبلغ نهایی قابل پرداخت پس از تخفیف."""
        return max(self.get_subtotal() - self.coupon_discount(user), Decimal('0'))

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


class Coupon(models.Model):
    """
    کد تخفیف.

    هر محدودیت اختیاری است و خالی گذاشتن آن یعنی «بدون محدودیت»؛ بنابراین این چهار حالت
    با همین مدل ساخته می‌شود:
      ۱. کد اختصاصی یک کاربر (user پر، course خالی) با بازه زمانی مشخص
      ۲. کد همگانی برای یک دوره مشخص (user خالی، course پر) با بازه زمانی مشخص
      ۳. کد همگانی برای همه محصولات (user و course خالی، بدون تاریخ)
      ۴. کد همگانی زمان‌دار برای همه محصولات (user و course خالی + valid_from/valid_until)

    فعال یا غیرفعال کردن هر کد با فیلد is_active و از پنل ادمین انجام می‌شود.
    """

    PERCENT = 'percent'
    FIXED = 'fixed'
    DISCOUNT_TYPE_CHOICES = [
        (PERCENT, 'درصدی'),
        (FIXED, 'مبلغ ثابت (تومان)'),
    ]

    code = models.CharField(
        max_length=40,
        unique=True,
        verbose_name='کد تخفیف',
        help_text='به بزرگی/کوچکی حروف حساس نیست و هنگام ذخیره یکسان‌سازی می‌شود.',
    )
    title = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='عنوان / یادداشت',
        help_text='برای شناسایی راحت‌تر کد در پنل ادمین.',
    )
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
        default=PERCENT,
        verbose_name='نوع تخفیف',
    )
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='مقدار تخفیف',
        help_text='درصدی: عددی بین ۰ تا ۱۰۰ — مبلغ ثابت: مبلغ به تومان.',
    )
    max_discount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name='سقف تخفیف (تومان)',
        help_text='فقط برای تخفیف درصدی؛ خالی یعنی بدون سقف.',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='coupons',
        verbose_name='کاربر اختصاصی',
        help_text='خالی یعنی برای همه کاربران.',
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='coupons',
        verbose_name='دوره اختصاصی',
        help_text='خالی یعنی برای همه محصولات.',
    )
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='شروع بازه اعتبار',
        help_text='خالی یعنی از ابتدا معتبر است.',
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='پایان بازه اعتبار',
        help_text='خالی یعنی بدون تاریخ انقضا.',
    )
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='سقف کل استفاده',
        help_text='خالی یعنی تعداد نامحدود.',
    )
    per_user_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=1,
        verbose_name='سقف استفاده هر کاربر',
        help_text='خالی یعنی برای هر کاربر نامحدود.',
    )
    used_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name='تعداد استفاده موفق',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال',
        help_text='برای غیرفعال کردن موقت کد بدون حذف آن را بردارید.',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'کد تخفیف'
        verbose_name_plural = 'کدهای تخفیف'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} ({self.get_discount_type_display()})'

    def save(self, *args, **kwargs):
        self.code = (self.code or '').strip().upper()
        super().save(*args, **kwargs)

    def clean(self):
        self.code = (self.code or '').strip().upper()
        errors = {}
        value = self.value or Decimal('0')
        if self.discount_type == self.PERCENT and not (Decimal('0') < value <= Decimal('100')):
            errors['value'] = 'برای تخفیف درصدی، مقدار باید بزرگ‌تر از ۰ و حداکثر ۱۰۰ باشد.'
        if self.discount_type == self.FIXED and value <= 0:
            errors['value'] = 'مبلغ تخفیف باید بزرگ‌تر از صفر باشد.'
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            errors['valid_until'] = 'پایان بازه اعتبار باید بعد از شروع آن باشد.'
        if errors:
            raise ValidationError(errors)

    def active_error(self, now=None):
        """اگر کد در این لحظه قابل استفاده نباشد، پیام خطای فارسی برمی‌گرداند."""
        if not self.is_active:
            return 'این کد تخفیف توسط مدیر غیرفعال شده است.'
        now = now or timezone.now()
        if self.valid_from and now < self.valid_from:
            return 'زمان استفاده از این کد تخفیف هنوز شروع نشده است.'
        if self.valid_until and now > self.valid_until:
            return 'مهلت استفاده از این کد تخفیف به پایان رسیده است.'
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return 'ظرفیت استفاده از این کد تخفیف تکمیل شده است.'
        return ''

    def is_available_to_user(self, user):
        """کد اختصاصی فقط برای همان کاربر معتبر است."""
        if self.user_id is None:
            return True
        return bool(user and user.is_authenticated and user.pk == self.user_id)

    def usage_count_for(self, user):
        """تعداد استفاده موفق این کاربر از کد."""
        if not user or not user.is_authenticated:
            return 0
        return self.redemptions.filter(user=user).count()

    def discount_for(self, amount):
        """مبلغ تخفیف روی یک مبلغ مشخص، با احتساب سقف و بدون عبور از خود مبلغ."""
        amount = Decimal(amount or 0)
        if amount <= 0:
            return Decimal('0')
        if self.discount_type == self.PERCENT:
            discount = amount * Decimal(self.value or 0) / Decimal('100')
        else:
            discount = Decimal(self.value or 0)
        if self.max_discount is not None:
            discount = min(discount, Decimal(self.max_discount))
        discount = min(discount, amount)
        discount = discount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return min(discount, amount)

    def validate_for_cart(self, cart, user, now=None):
        """
        بررسی اعتبار کد برای یک سبد خرید.

        خروجی: (مبلغ تخفیف, پیام خطا)؛ در صورت خطا مبلغ تخفیف None است.
        """
        message = self.active_error(now)
        if message:
            return None, message
        if not self.is_available_to_user(user):
            return None, 'این کد تخفیف فقط برای کاربر مشخصی قابل استفاده است.'
        if self.per_user_limit is not None and self.usage_count_for(user) >= self.per_user_limit:
            return None, 'شما قبلاً از این کد تخفیف استفاده کرده‌اید.'
        items = list(cart.items.select_related('course'))
        if not items:
            return None, 'سبد خرید شما خالی است؛ ابتدا دوره‌ای به سبد خرید اضافه کنید.'
        if self.course_id is not None:
            eligible = [item for item in items if item.course_id == self.course_id]
            if not eligible:
                return None, f'این کد تخفیف فقط برای دوره «{self.course.title}» است و آن دوره در سبد خرید نیست.'
        else:
            eligible = [item for item in items if item.course.price > 0]
        base = sum((item.course.price for item in eligible), Decimal('0'))
        if base <= 0:
            return None, 'این کد تخفیف روی محصولات فعلی سبد خرید قابل اعمال نیست.'
        discount = self.discount_for(base)
        if discount <= 0:
            return None, 'این کد تخفیف مبلغی از سبد خرید کم نمی‌کند.'
        return discount, ''


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
    subtotal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='مبلغ پیش از تخفیف (تومان)',
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='مبلغ تخفیف (تومان)',
    )
    coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='کد تخفیف',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
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


class CouponRedemption(models.Model):
    """سابقه استفاده موفق از یک کد تخفیف (برای محدودیت تعداد استفاده)."""

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='redemptions',
        verbose_name='کد تخفیف',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coupon_redemptions',
        verbose_name='کاربر',
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='coupon_redemptions',
        verbose_name='سفارش',
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='مبلغ تخفیف (تومان)',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ استفاده')

    class Meta:
        verbose_name = 'استفاده از کد تخفیف'
        verbose_name_plural = 'استفاده‌های کد تخفیف'
        ordering = ['-created_at']
        unique_together = ('coupon', 'order')

    def __str__(self):
        return f'{self.coupon.code} — {self.user} — سفارش #{self.order_id}'


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
