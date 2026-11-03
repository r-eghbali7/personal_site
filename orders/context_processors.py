"""
Context Processor: cart_processor
اضافه کردن اطلاعات سبد خرید به context همه templateها
"""

from django.db.models import Count

from .models import Cart


def cart_processor(request):
    """اطلاعات سبد خرید را با حداقل کوئری در context همه صفحات قرار می‌دهد."""
    cart = None

    if request.user.is_authenticated:
        cart = (
            Cart.objects.filter(user=request.user)
            .annotate(items_count=Count('items'))
            .first()
        )
    elif request.session.session_key:
        cart = (
            Cart.objects.filter(session_key=request.session.session_key)
            .annotate(items_count=Count('items'))
            .first()
        )

    return {
        'cart': cart,
        'cart_count': getattr(cart, 'items_count', 0) if cart else 0,
    }
