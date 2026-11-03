"""
Context processor: banners — بنرهای فعال را در تمام قالب‌ها در دسترس قرار می‌دهد
"""

from .models import Banner


def active_banners(request):
    """
    همه بنرهای فعال را با ترتیب نمایش برمی‌گرداند.
    """
    return {
        'active_banners': Banner.objects.filter(is_active=True),
    }
