"""فیلترهای نمایش محتوای غنی (ادیتور) در قالب‌های دوره."""

import re

from django import template
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe

register = template.Library()

_BLOCK_TAG_RE = re.compile(
    r'<(p|h[1-6]|ul|ol|li|div|blockquote|figure|img|iframe|video|table|section|pre)\b',
    re.IGNORECASE,
)

FEATURE_ICON_MAP = {
    'infinity': 'all_inclusive',
    'folder-down': 'folder_zip',
    'laptop': 'laptop_mac',
    'headset': 'headset_mic',
    'monitor-play': 'play_circle',
    'refresh-cw': 'sync',
    'clipboard-check': 'assignment_turned_in',
    'award': 'workspace_premium',
    'clock': 'schedule',
    'users': 'groups',
}


@register.filter
def rich_text(value):
    """
    محتوای نوشته‌شده با ادیتور را برای نمایش آماده می‌کند.

    اگر محتوا HTML باشد به‌صورت امن برگردانده می‌شود؛ اگر متن ساده باشد
    (محتوای قدیمی) خطوط جدید به <br> تبدیل می‌شوند.
    """
    if not value:
        return ''
    if _BLOCK_TAG_RE.search(str(value)):
        return mark_safe(value)
    return linebreaks(value)


@register.filter
def course_feature_icon(value):
    """Translate common Lucide icon IDs to Material Symbols names."""
    if not value:
        return ''
    return FEATURE_ICON_MAP.get(str(value).strip().lower(), value)
