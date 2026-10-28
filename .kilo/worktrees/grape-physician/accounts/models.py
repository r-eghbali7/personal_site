"""
App: accounts — مدل‌های کاربر سفارشی و OTP

CustomUser: ورود با شماره موبایل به‌جای username
OTPCode: ذخیره کد تأیید ارسال‌شده از کاوه‌نگار
"""

import random
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta


class CustomUserManager(BaseUserManager):
    """Manager سفارشی برای مدیریت کاربران با شماره موبایل."""

    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('شماره موبایل الزامی است.')
        user = self.model(phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(phone_number, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    مدل کاربر سفارشی.
    فیلد اصلی ورود: phone_number
    """

    phone_number = models.CharField(
        max_length=11,
        unique=True,
        verbose_name='شماره موبایل',
    )
    full_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='نام و نام‌خانوادگی',
    )
    email = models.EmailField(
        blank=True,
        verbose_name='ایمیل',
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='تصویر پروفایل',
    )
    bio = models.TextField(
        blank=True,
        verbose_name='درباره من',
    )

    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_staff = models.BooleanField(default=False, verbose_name='کارمند')
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ عضویت')

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return self.full_name or self.phone_number

    def get_enrolled_courses(self):
        """دوره‌های خریداری‌شده کاربر."""
        return self.enrollments.filter(is_active=True).select_related('course')


class OTPCode(models.Model):
    """
    کد یکبارمصرف OTP.
    هر درخواست، یک رکورد جدید ایجاد می‌کند.
    """

    phone_number = models.CharField(
        max_length=11,
        verbose_name='شماره موبایل',
    )
    code = models.CharField(
        max_length=6,
        verbose_name='کد تأیید',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    expires_at = models.DateTimeField(verbose_name='زمان انقضا')
    is_used = models.BooleanField(default=False, verbose_name='استفاده شده')

    class Meta:
        verbose_name = 'کد OTP'
        verbose_name_plural = 'کدهای OTP'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.phone_number} — {self.code}'

    def save(self, *args, **kwargs):
        if not self.pk:
            from django.conf import settings
            minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
            self.expires_at = timezone.now() + timedelta(minutes=minutes)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """بررسی اعتبار کد: منقضی نشده و استفاده نشده باشد."""
        return not self.is_used and self.expires_at > timezone.now()

    @classmethod
    def generate_code(cls):
        """تولید کد ۶ رقمی تصادفی."""
        return str(random.randint(100000, 999999))

    @classmethod
    def create_for_phone(cls, phone_number):
        """
        ابطال کدهای قبلی و ایجاد کد جدید برای شماره.
        Returns: OTPCode instance
        """
        cls.objects.filter(phone_number=phone_number, is_used=False).update(is_used=True)
        code = cls.generate_code()
        return cls.objects.create(phone_number=phone_number, code=code)
