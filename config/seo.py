from django.http import HttpResponse
from django.urls import reverse


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse('sitemap'))
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
