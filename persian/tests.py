from datetime import date, datetime

from django.test import TestCase
from django.utils import timezone

from .templatetags.persian_filters import (
    gregorian_to_jalali,
    persian_date,
    persian_number,
)


class JalaliConversionTests(TestCase):
    def test_known_gregorian_dates_convert_to_jalali(self):
        self.assertEqual(gregorian_to_jalali(2026, 3, 21), (1405, 1, 1))
        self.assertEqual(gregorian_to_jalali(2026, 4, 6), (1405, 1, 17))
        self.assertEqual(gregorian_to_jalali(2026, 10, 28), (1405, 8, 6))
        self.assertEqual(gregorian_to_jalali(2025, 3, 21), (1404, 1, 1))
        self.assertEqual(gregorian_to_jalali(2024, 3, 20), (1403, 1, 1))

    def test_persian_date_filter_returns_jalali_with_persian_digits(self):
        value = timezone.make_aware(datetime(2026, 4, 6, 12, 0))

        self.assertEqual(persian_date(value, "%Y %B %d"), "۱۴۰۵ فروردین ۱۷")
        self.assertEqual(persian_date(value, "%d %B %Y"), "۱۷ فروردین ۱۴۰۵")
        self.assertEqual(persian_date(date(2026, 3, 21)), "۱۴۰۵/۰۱/۰۱")

    def test_persian_date_handles_empty_values(self):
        self.assertEqual(persian_date(None), "")
        self.assertEqual(persian_date(""), "")

    def test_persian_number_converts_digits_without_grouping(self):
        self.assertEqual(persian_number(18), "۱۸")
        self.assertEqual(persian_number(1405), "۱۴۰۵")
