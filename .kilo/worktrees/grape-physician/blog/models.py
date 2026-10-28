"""
App: blog — مدل‌های وبلاگ و کامنت
"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify


class BlogPost(models.Model):
    """مقاله وبلاگ."""

    title = models.CharField(max_length=300, verbose_name='عنوان')
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name='اسلاگ')
    summary = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='خلاصه مقاله',
    )
    content = models.TextField(verbose_name='محتوای مقاله')
    thumbnail = models.ImageField(
        upload_to='blog/thumbnails/',
        blank=True,
        null=True,
        verbose_name='تصویر شاخص',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog_posts',
        verbose_name='نویسنده',
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='دسته‌بندی',
    )
    tags = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='تگ‌ها',
        help_text='با ویرگول جدا کنید.',
    )
    views_count = models.PositiveIntegerField(default=0, verbose_name='بازدید')
    read_time_minutes = models.PositiveIntegerField(
        default=5,
        verbose_name='زمان مطالعه (دقیقه)',
    )
    is_published = models.BooleanField(default=False, verbose_name='منتشر شده')
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ انتشار',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'مقاله'
        verbose_name_plural = 'مقالات'
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def get_tags_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])


class Comment(models.Model):
    """کامنت مقاله."""

    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='مقاله',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog_comments',
        verbose_name='کاربر',
    )
    body = models.TextField(verbose_name='متن نظر')
    is_approved = models.BooleanField(
        default=False,
        verbose_name='تأیید شده',
        help_text='کامنت باید توسط ادمین تأیید شود.',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ارسال')

    class Meta:
        verbose_name = 'نظر'
        verbose_name_plural = 'نظرات'
        ordering = ['created_at']

    def __str__(self):
        return f'نظر {self.user} روی "{self.post.title[:40]}"'
