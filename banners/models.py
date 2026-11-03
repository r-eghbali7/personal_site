"""
App: banners — مدیریت بنرهای تبلیغاتی سایت

Banner: تصویر بنر، لینک مقصد، عنوان، وضعیت فعال/غیرفعال و ترتیب نمایش
"""

from django.db import models


class Banner(models.Model):
    """
    مدل بنر سایت.
    از طریق پنل مدیریت/apache می‌توان تصویر، لینک مقصد و ترتیب را تعریف کرد.
    """

    title = models.CharField(
        max_length=150,
        verbose_name='عنوان بنر',
        blank=True,
        help_text='عنوان نمایشی بنر (اختیاری)',
    )
    image = models.ImageField(
        upload_to='banners/',
        verbose_name='تصویر بنر',
        help_text='فایل تصویر بنر را آپلود کنید',
    )
    link_url = models.URLField(
        verbose_name='لینک مقصد',
        help_text='هنگام کلیک روی بنر به کدام صفحه هدایت شود؟',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال',
        help_text='Benr در سایت نمایش داده شود؟',
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتیب نمایش',
        help_text='عدد کوچک‌تر قبلاً نمایش داده می‌شود',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد',
    )

    class Meta:
        verbose_name = 'بنر'
        verbose_name_plural = 'بنرها'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title or f'Banner #{self.pk}'
