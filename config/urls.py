"""
Django URL Configuration for LMS آکادمی طاهری
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, register_converter

from . import error_views
from .seo import robots_txt
from .sitemaps import BlogPostSitemap, CourseSitemap, StaticViewSitemap
from config.converters import UnicodeSlugConverter

register_converter(UnicodeSlugConverter, 'uslug')

sitemaps = {
    'static': StaticViewSitemap,
    'courses': CourseSitemap,
    'blog': BlogPostSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('', include('courses.urls')),
    path('accounts/', include('accounts.urls')),
    path('orders/', include('orders.urls')),
    path('tickets/', include('tickets.urls')),
    path('blog/', include('blog.urls')),
    path('podcasts/', include('blog.podcast_urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('site-search/', include('search.urls')),
]

# صفحه‌های خطای سفارشی هماهنگ با ظاهر سایت
handler404 = 'config.error_views.handler_404'
handler403 = 'config.error_views.handler_403_as_404'
handler500 = 'config.error_views.handler_500'

# در حالت توسعه، فایل‌های ویدئوی آپلودشده در دیتابیس از پوشه media سرو می‌شوند.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# پیش‌نمایش صفحه‌های خطا در حالت توسعه (با DEBUG=False خودکار در دسترس است)
if settings.DEBUG:
    urlpatterns += [
        path('__errors__/404/', error_views.preview_404),
        path('__errors__/500/', error_views.preview_500),
    ]
