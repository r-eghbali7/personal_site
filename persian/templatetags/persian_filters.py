"""
Custom template filters for Persian localization.

Usage in templates:
    {% load persian_filters %}

    {{ value|persian_date:"Y/m/d" }}
    {{ price|persian_price }}
    {{ number|persian_int }}
"""

from datetime import date, datetime
from decimal import Decimal

try:
    import jdatetime
except ImportError:
    jdatetime = None

from django import template
from django.utils import timezone
from django.utils.formats import localize

register = template.Library()

# Persian (Farsi) digits ۰-۹
PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
PERSIAN_COMMA = "٬"

JALALI_MONTHS = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
]

_GREGORIAN_MONTH_DAYS = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]


def gregorian_to_jalali(gy, gm, gd):
    """
    تبدیل تاریخ میلادی به شمسی بدون وابستگی خارجی.

    پیاده‌سازی استاندارد (بر پایه الگوریتم jalaali-js)؛ در صورت نصب نبودن
    jdatetime از همین تابع استفاده می‌شود.
    """
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (
        (365 * gy)
        + ((gy2 + 3) // 4)
        - ((gy2 + 99) // 100)
        + ((gy2 + 399) // 400)
        - 80
        + gd
        + _GREGORIAN_MONTH_DAYS[gm - 1]
    )
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def _format_jalali(fmt, jy, jm, jd):
    """جایگزینی نشانه‌های تاریخ در قالب با مقادیر شمسی."""
    month = JALALI_MONTHS[jm - 1]
    replacements = {
        "%Y": str(jy),
        "%y": str(jy % 100).zfill(2),
        "%m": str(jm).zfill(2),
        "%d": str(jd).zfill(2),
        "%B": month,
        "%b": month,
    }
    formatted = fmt
    for token, replacement in replacements.items():
        formatted = formatted.replace(token, replacement)
    return formatted


def to_persian_digits(text):
    """Convert all ASCII digits 0-9 in *text* to Persian digits ۰-۹."""
    if text is None:
        return ""
    return str(text).translate(str.maketrans("0123456789", PERSIAN_DIGITS))


@register.filter
def persian_int(value):
    """Format an integer/number with Persian digits and 3-digit grouping."""
    if value in (None, ""):
        return ""
    # Handle Decimal / float / int
    if isinstance(value, Decimal):
        formatted = f"{value:,.0f}"
    elif isinstance(value, (int, float)):
        formatted = f"{value:,.0f}"
    else:
        formatted = str(value)
    # Replace thousands separator and digits
    parts = formatted.split(",")
    formatted = PERSIAN_COMMA.join(parts)
    return to_persian_digits(formatted)


@register.filter
def persian_price(value):
    """Format a price with Persian digits and 3-digit grouping (e.g., ۴,۹۰۰,۰۰۰)."""
    return persian_int(value)


@register.filter
def persian_date(value, fmt=None):
    """
    Convert a Gregorian datetime/date to Shamsi (Jalali) date with Persian digits.

    If *jdatetime* is not installed, falls back to the Gregorian date formatted
    with ``date_format`` (digits still converted to Persian).
    """
    if value in (None, ""):
        return ""

    if isinstance(value, str):
        # Try to parse common datetime strings
        for parser_fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                value = datetime.strptime(value, parser_fmt)
                break
            except (ValueError, TypeError):
                continue
        else:
            return to_persian_digits(value)

    if isinstance(value, datetime) and jdatetime:
        if value.tzinfo is not None:
            value = timezone.localtime(value)
        jdt = jdatetime.datetime.fromgregorian(datetime=value)
        if fmt:
            formatted = jdt.strftime(fmt)
        else:
            formatted = jdt.strftime("%Y/%m/%d")
        return to_persian_digits(formatted)

    if isinstance(value, date) and jdatetime:
        jdt = jdatetime.date.fromgregorian(date=value)
        if fmt:
            formatted = jdt.strftime(fmt)
        else:
            formatted = jdt.strftime("%Y/%m/%d")
        return to_persian_digits(formatted)

    # Fallback (jdatetime نصب نیست): تبدیل داخلی میلادی به شمسی
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = timezone.localtime(value)
        gy, gm, gd = value.year, value.month, value.day
    elif isinstance(value, date):
        gy, gm, gd = value.year, value.month, value.day
    else:
        return to_persian_digits(value)

    jy, jm, jd = gregorian_to_jalali(gy, gm, gd)
    if fmt:
        formatted = _format_jalali(fmt, jy, jm, jd)
    else:
        formatted = f"{jy}/{jm:02d}/{jd:02d}"
    return to_persian_digits(formatted)


@register.filter
def persian_datetime(value, fmt=None):
    """Alias for ``persian_date``."""
    return persian_date(value, fmt)


@register.filter
def persian_number(value):
    """Convert digits to Persian without grouping (e.g., 1234 → ۱۲۳۴)."""
    if value in (None, ""):
        return ""
    return to_persian_digits(str(value))
