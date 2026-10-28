"""
App: tickets — مدل‌های سیستم تیکت پشتیبانی
"""

from django.db import models
from django.conf import settings


class Ticket(models.Model):
    """تیکت پشتیبانی ارسال‌شده توسط کاربر."""

    STATUS_CHOICES = [
        ('open', 'باز'),
        ('in_progress', 'در حال بررسی'),
        ('closed', 'بسته شده'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'کم'),
        ('medium', 'متوسط'),
        ('high', 'زیاد'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name='کاربر',
    )
    subject = models.CharField(max_length=300, verbose_name='موضوع')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name='وضعیت',
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='اولویت',
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name='دوره مرتبط',
        help_text='اختیاری — اگر تیکت درباره دوره خاصی است.',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'تیکت'
        verbose_name_plural = 'تیکت‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.pk} — {self.subject[:60]}'

    def get_last_message(self):
        return self.messages.order_by('-sent_at').first()


class TicketMessage(models.Model):
    """پیام داخل یک تیکت — می‌تواند از کاربر یا پشتیبان باشد."""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='تیکت',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ticket_messages',
        verbose_name='فرستنده',
    )
    body = models.TextField(verbose_name='متن پیام')
    attachment = models.FileField(
        upload_to='tickets/attachments/',
        blank=True,
        null=True,
        verbose_name='فایل پیوست',
    )
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ارسال')

    class Meta:
        verbose_name = 'پیام تیکت'
        verbose_name_plural = 'پیام‌های تیکت'
        ordering = ['sent_at']

    def __str__(self):
        return f'پیام از {self.sender} در تیکت #{self.ticket.pk}'
