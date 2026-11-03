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
