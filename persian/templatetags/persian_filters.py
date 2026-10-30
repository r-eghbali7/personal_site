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

    # Fallback (no jdatetime installed): just convert digits
    fallback_fmt = fmt or "%Y/%m/%d"
    try:
        formatted = value.strftime(fallback_fmt)
    except (AttributeError, ValueError):
        formatted = str(value)
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
