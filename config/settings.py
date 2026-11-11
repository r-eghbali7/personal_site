"""
Django Settings — LMS آکادمی طاهری
"""

from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# ──────────────────────────────────────────────────────────────
# SECURITY
# ──────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'development-only-change-before-deploying')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
    if host.strip()
]

if not DEBUG and SECRET_KEY == 'development-only-change-before-deploying':
    raise RuntimeError('DJANGO_SECRET_KEY must be configured when DJANGO_DEBUG is disabled.')

# ──────────────────────────────────────────────────────────────
# PRODUCTION SECURITY
# ──────────────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = os.environ.get(
    'DJANGO_SECURE_SSL_REDIRECT', str(not DEBUG)
).lower() in ('1', 'true', 'yes')
SECURE_HSTS_SECONDS = int(os.environ.get(
    'DJANGO_SECURE_HSTS_SECONDS', '31536000' if not DEBUG else '0'
))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
    'DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False'
).lower() in ('1', 'true', 'yes')
SECURE_HSTS_PRELOAD = os.environ.get(
    'DJANGO_SECURE_HSTS_PRELOAD', 'False'
).lower() in ('1', 'true', 'yes')
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
X_FRAME_OPTIONS = 'DENY'

# Enable only when a trusted reverse proxy overwrites X-Forwarded-Proto.
if os.environ.get('DJANGO_SECURE_PROXY_SSL_HEADER', 'False').lower() in ('1', 'true', 'yes'):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Authentication and OTP abuse limits. Rates use django-ratelimit syntax.
RATELIMIT_LOGIN_IP = '10/m'
RATELIMIT_LOGIN_PHONE = '5/m'
RATELIMIT_REGISTER_IP = '5/h'
RATELIMIT_REGISTER_PHONE = '3/h'
RATELIMIT_OTP_VERIFY_IP = '10/m'
RATELIMIT_OTP_VERIFY_PHONE = '5/m'
RATELIMIT_OTP_RESEND_IP = '3/h'
RATELIMIT_OTP_RESEND_PHONE = '3/h'
RATELIMIT_FORGOT_PASSWORD_IP = '5/h'
RATELIMIT_FORGOT_PASSWORD_PHONE = '3/h'
RATELIMIT_PASSWORD_RESET_IP = '5/h'
RATELIMIT_PASSWORD_RESET_PHONE = '5/h'
RATELIMIT_IP_META_KEY = os.environ.get('DJANGO_RATELIMIT_IP_META_KEY', 'REMOTE_ADDR')

# ──────────────────────────────────────────────────────────────
# APPLICATIONS
# ──────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    # ادیتور محتوای وبلاگ
    'django_ckeditor_5',
    # Local Apps
    'accounts',
    'courses',
    'orders',
    'tickets',
    'blog',
    'persian',
    'search',
    'banners',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # بنرهای فعال
                'banners.context_processors.active_banners',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ──────────────────────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ──────────────────────────────────────────────────────────────
# AUTH — کاربر سفارشی
# ──────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.CustomUser'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.PhoneAuthBackend',
    'django.contrib.auth.backends.ModelBackend',  # fallback برای ادمین
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ──────────────────────────────────────────────────────────────
# INTERNATIONALIZATION
# ──────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# ──────────────────────────────────────────────────────────────
# STATIC & MEDIA FILES
# ──────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CKEDITOR_5_CONFIGS = {
    'default': {
        'language': 'fa',
        'toolbar': {
            'items': [
                'heading', '|', 'bold', 'italic', 'underline', '|',
                'bulletedList', 'numberedList', '|', 'link', 'insertImage',
                'mediaEmbed', 'insertTable', 'htmlEmbed', '|', 'undo', 'redo',
            ],
        },
    },
}
CKEDITOR_5_CONFIGS['extends'] = CKEDITOR_5_CONFIGS['default']
CKEDITOR_5_FILE_UPLOAD_PERMISSION = 'staff'
CKEDITOR_5_MAX_FILE_SIZE = 50

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ──────────────────────────────────────────────────────────────
# SESSION
# ──────────────────────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 روز

# ──────────────────────────────────────────────────────────────
# OTP — کاوه‌نگار
# ──────────────────────────────────────────────────────────────
KAVENEGAR_API_KEY = os.environ.get('KAVENEGAR_API_KEY', '')
OTP_EXPIRY_MINUTES = 5

# ──────────────────────────────────────────────────────────────
# ZARINPAL — درگاه پرداخت
# ──────────────────────────────────────────────────────────────
ZARINPAL_MERCHANT_ID = os.environ.get('ZARINPAL_MERCHANT_ID', '')
ZARINPAL_SANDBOX = os.environ.get('ZARINPAL_SANDBOX', 'False').lower() in ('1', 'true', 'yes')

# ──────────────────────────────────────────────────────────────
# EMAIL — خبرنامه و کد تخفیف
# ──────────────────────────────────────────────────────────────
_default_backend = (
    'django.core.mail.backends.smtp.EmailBackend'
    if os.environ.get('EMAIL_HOST_USER')
    else ('django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend')
)
EMAIL_BACKEND = os.environ.get('DJANGO_EMAIL_BACKEND', _default_backend)
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'True').lower() in ('1', 'true', 'yes')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'noreply@example.com')
# ──────────────────────────────────────────────────────────────
# MESSAGES
# ──────────────────────────────────────────────────────────────
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}
