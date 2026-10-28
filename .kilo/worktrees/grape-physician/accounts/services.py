"""
سرویس ارسال OTP از طریق کاوه‌نگار

مستندات API: https://app.kavenegar.com/wiki/API/Send
"""

import requests
from django.conf import settings


class KavenegarService:
    """کلاینت ساده برای ارسال پیامک از طریق API کاوه‌نگار."""

    BASE_URL = 'https://api.kavenegar.com/v1/{api_key}/verify/lookup.json'

    def __init__(self):
        self.api_key = settings.KAVENEGAR_API_KEY

    def send_otp(self, phone_number: str, code: str) -> dict:
        """
        ارسال کد OTP با استفاده از قالب تأیید کاوه‌نگار.

        Args:
            phone_number: شماره گیرنده (۰۹xxxxxxxxx)
            code: کد ۶ رقمی

        Returns:
            dict با کلیدهای: success (bool), message (str)
        """
        url = self.BASE_URL.format(api_key=self.api_key)
        payload = {
            'receptor': phone_number,
            'token': code,
            'template': 'verify',   # نام قالب پیامک تعریف‌شده در پنل کاوه‌نگار
        }
        try:
            response = requests.post(url, data=payload, timeout=10)
            data = response.json()

            if response.status_code == 200 and data.get('return', {}).get('status') == 200:
                return {'success': True, 'message': 'کد با موفقیت ارسال شد.'}
            else:
                error_msg = data.get('return', {}).get('message', 'خطا در ارسال پیامک')
                return {'success': False, 'message': error_msg}

        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'اتصال به سرویس پیامک با خطا روبرو شد (timeout).'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'message': f'خطای شبکه: {str(e)}'}
        except Exception as e:
            return {'success': False, 'message': f'خطای ناشناخته: {str(e)}'}


def send_otp_code(phone_number: str, code: str) -> dict:
    """تابع shortcut برای استفاده در View‌ها."""
    service = KavenegarService()
    return service.send_otp(phone_number, code)
