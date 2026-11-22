"""آماده‌سازی محتوای مقاله: تبدیل به HTML امن و ساخت فهرست سرفصل‌ها."""

import re
from html import unescape

from django.utils.html import linebreaks
from django.utils.safestring import mark_safe
from django.utils.text import slugify

_HEADING_RE = re.compile(r'<h([1-6])([^>]*)>(.*?)</h\1>', re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r'<[^>]+>')
_BLOCK_TAG_RE = re.compile(
    r'<(p|h[1-6]|ul|ol|li|div|blockquote|figure|img|iframe|video|table|section|pre)\b',
    re.IGNORECASE,
)
_ID_ATTR_RE = re.compile(r'\sid=("[^"]*"|\'[^\']*\')', re.IGNORECASE)
_TABLE_RE = re.compile(r'<table\b[^>]*>.*?</table>', re.IGNORECASE | re.DOTALL)
_TR_RE = re.compile(r'<tr\b[^>]*>.*?</tr>', re.IGNORECASE | re.DOTALL)
_TH_RE = re.compile(r'<th\b', re.IGNORECASE)
_TD_OPEN_RE = re.compile(r'<td(?=[\s>])', re.IGNORECASE)
_TD_CLOSE_RE = re.compile(r'</td\s*>', re.IGNORECASE)


def article_content_and_toc(content):
    """
    محتوای مقاله را برای نمایش آماده می‌کند.

    خروجی: (html, toc)
      - html: اگر محتوا متن ساده باشد با linebreaks و اگر HTML باشد به‌صورت امن.
      - toc: فهرست سرفصل‌های h2/h3/h4 با شناسه یکتای هر سرتیتر برای لینک‌دهی.

    برای هر سرتیتر یک id یکتا ساخته می‌شود تا فهرست سرفصل‌ها به آن لینک بدهد.
    """
    if not content:
        return '', []

    # محتوای قدیمی/ساده که تگ بلوکی ندارد.
    if not _BLOCK_TAG_RE.search(content):
        return linebreaks(content), []

    toc = []
    used_ids = {}

    def replace_heading(match):
        level = int(match.group(1))
        attributes = match.group(2) or ''
        inner = match.group(3)
        text = unescape(_TAG_RE.sub('', inner)).strip()
        if not text:
            return match.group(0)

        base = slugify(text, allow_unicode=True)[:60] or f'heading-{len(toc) + 1}'
        count = used_ids.get(base, 0) + 1
        used_ids[base] = count
        anchor = base if count == 1 else f'{base}-{count}'

        attributes = _ID_ATTR_RE.sub('', attributes)
        toc.append({
            'level': level,
            'text': text,
            'id': anchor,
            'indent': max(0, level - 2) * 14,
        })
        return f'<h{level}{attributes} id="{anchor}">{inner}</h{level}>'

    html = _HEADING_RE.sub(replace_heading, content)
    html = ensure_table_headers(html)
    return mark_safe(html), toc


def _add_table_header_cells(table_html):
    """اولین ردیف جدول را به سرصفحهٔ ستون تبدیل می‌کند."""
    if _TH_RE.search(table_html):
        return table_html
    row_match = _TR_RE.search(table_html)
    if not row_match:
        return table_html
    row = row_match.group(0)
    if not _TD_OPEN_RE.search(row):
        return table_html
    fixed_row = _TD_OPEN_RE.sub('<th scope="col"', row)
    fixed_row = _TD_CLOSE_RE.sub('</th>', fixed_row)
    return table_html.replace(row, fixed_row, 1)


def ensure_table_headers(html):
    """
    جدول‌های ادیتور معمولاً ردیف عنوان را با <td> می‌سازند و همین باعث
    خطای دسترس‌پذیری td-has-header می‌شود؛ ردیف اول را به <th scope="col">
    تبدیل می‌کنیم (فقط وقتی جدول هیچ <th> ندارد).
    """
    if not html or '<table' not in html.lower():
        return html
    return _TABLE_RE.sub(lambda match: _add_table_header_cells(match.group(0)), html)
