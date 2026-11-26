from urllib.parse import urlsplit

from django.http import HttpResponse
from django.urls import reverse

LOCAL_HOSTNAMES = {'localhost', '127.0.0.1', '0.0.0.0', '::1', 'testserver'}


def canonical_origin(request):
    """مبدأ ثابت سایت (scheme + host) برای canonical، og:url و داده ساختاریافته.

    روی دامنهٔ واقعی همیشه https برمی‌گردد؛ بنابراین حتی اگر پروکسی هدر
    X-Forwarded-Proto را نگذارد یا نسخهٔ http بالا بیاید، نسخهٔ http به‌عنوان
    نسخهٔ اصلی به گوگل معرفی نمی‌شود. روی هاست محلی، scheme خود درخواست حفظ می‌شود.
    """
    host = request.get_host()
    hostname = urlsplit(f'//{host}').hostname or host
    if hostname in LOCAL_HOSTNAMES:
        return f'{request.scheme}://{host}'
    return f'https://{host}'


def site_origin(request):
    return {'site_origin': canonical_origin(request)}


def robots_txt(request):
    sitemap_url = f"{canonical_origin(request)}{reverse('sitemap')}"
    content = '\n'.join(
        [
            'User-agent: *',
            'Allow: /',
            'Disallow: /accounts/',
            'Disallow: /admin/',
            'Disallow: /ckeditor5/',
            'Disallow: /orders/',
            'Disallow: /site-search/',
            'Disallow: /tickets/',
            'Disallow: /quiz/',
            'Disallow: /*/chapters/',
            'Disallow: /*/lessons/',
            f'Sitemap: {sitemap_url}',
            '',
        ]
    )
    return HttpResponse(content, content_type='text/plain; charset=utf-8')
