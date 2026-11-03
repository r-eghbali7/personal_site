"""نمایش صفحه‌های خطای سفارشی هماهنگ با ظاهر سایت."""

from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template import TemplateDoesNotExist, loader


def handler_404(request, exception=None):
    """صفحه ۴۰۴ سفارشی."""
    return render(request, '404.html', status=404)


def handler_403_as_404(request, exception=None):
    """
    هر خطای دسترسی (۴۰۳) به‌جای «Forbidden» با صفحه ۴۰۴ نمایش داده می‌شود
    تا وجود محتوا برای کاربر غیرمجاز لو نرود.
    """
    return render(request, '404.html', status=404)


def handler_500(request):
    """
    صفحه ۵۰۰ سفارشی.

    بدون context رندر می‌شود تا اگر خطا از سمت دیتابیس یا context processorها باشد،
    خود صفحه خطا هم دچار خطا نشود.
    """
    try:
        template = loader.get_template('500.html')
    except TemplateDoesNotExist:
        return HttpResponseServerError('Internal Server Error')
    return HttpResponseServerError(template.render())


def preview_404(request):
    """پیش‌نمایش صفحه ۴۰۴ در حالت توسعه (فقط از طریق آدرس‌های DEBUG)."""
    return render(request, '404.html', status=404)


def preview_500(request):
    """پیش‌نمایش صفحه ۵۰۰ در حالت توسعه (فقط از طریق آدرس‌های DEBUG)."""
    try:
        template = loader.get_template('500.html')
    except TemplateDoesNotExist:
        return HttpResponseServerError('Internal Server Error')
    return HttpResponseServerError(template.render())
