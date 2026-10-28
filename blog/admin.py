"""
Admin: blog
"""

from django.contrib import admin
from .models import BlogCouponClaim, BlogPost, Comment


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('user', 'created_at')
    fields = ('user', 'body', 'is_approved', 'created_at')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_published', 'views_count', 'published_at')
    list_filter = ('is_published', 'category', 'published_at')
    search_fields = ('title', 'content', 'author__phone_number')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_published',)
    inlines = [CommentInline]
    readonly_fields = ('views_count', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'summary', 'content', 'thumbnail', 'author', 'category', 'tags')}),
        ('پیشنهادهای مرتبط', {'fields': (
            'architecture_quiz_title',
            'architecture_quiz_description',
            'podcast_title',
            'podcast_description',
            'podcast_audio_url',
            'podcast_duration_minutes',
            'coupon_discount_percent',
        )}),
        ('انتشار و آمار', {'fields': ('read_time_minutes', 'is_published', 'published_at', 'views_count', 'created_at', 'updated_at')}),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    list_editable = ('is_approved',)
    search_fields = ('user__phone_number', 'body')


@admin.register(BlogCouponClaim)
class BlogCouponClaimAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'coupon_code', 'discount_percent', 'post', 'verified_at')
    list_filter = ('discount_percent', 'verified_at')
    search_fields = ('phone_number', 'coupon_code')
    readonly_fields = ('phone_number', 'coupon_code', 'discount_percent', 'post', 'verified_at')
