"""
Context Processor: cart_processor
اضافه کردن اطلاعات سبد خرید به context همه templateها
"""

from .models import Cart


def cart_processor(request):
    """اطلاعات سبد خرید را در context همه صفحات قرار می‌دهد."""
    cart = None
    cart_count = 0

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    elif request.session.session_key:
        cart = Cart.objects.filter(session_key=request.session.session_key).first()

    if cart:
        cart_count = cart.get_items_count()

    return {
        'cart': cart,
        'cart_count': cart_count,
    }
