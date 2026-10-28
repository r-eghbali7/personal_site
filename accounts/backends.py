"""
Backend احراز هویت سفارشی

جنگو به‌صورت پیش‌فرض با username کار می‌کند.
این backend به جنگو می‌گوید با phone_number احراز هویت کند.
"""

from .models import CustomUser


class PhoneAuthBackend:
    """Backend احراز هویت بر اساس شماره موبایل."""

    def authenticate(self, request, phone_number=None, password=None, **kwargs):
        try:
            user = CustomUser.objects.get(phone_number=phone_number)
        except CustomUser.DoesNotExist:
            return None

        if user.check_password(password) and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
