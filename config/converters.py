"""Custom URL converters supporting Unicode (Persian) slugs."""
import re


class UnicodeSlugConverter:
    regex = r'[-\w]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
