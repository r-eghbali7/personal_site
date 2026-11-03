"""
Admin: banners — مدیریت بنرها از طریق داشبورد ادمینjango
"""

from django.contrib import admin
from .models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_tag', 'link_url', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'link_url')
    ordering = ['order', '-created_at']

    def image_tag(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="60" height="40" style="object-fit:cover;border-radius:6px;" />'
        return '—'
    image_tag.short_description = 'تصویر'
    image_tag.allow_tags = True
