"""
Django Settings — LMS آکادمی طاهری
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

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
# APPLICATIONS
# ──────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Local Apps
    'accounts',
    'courses',
    'orders',
    'tickets',
    'blog',
    'persian',
    'search',
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
                # Context processor سفارشی برای سبد خرید
                'orders.context_processors.cart_processor',
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ──────────────────────────────────────────────────────────────
# SESSION
# ──────────────────────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 روز

# ──────────────────────────────────────────────────────────────
# OTP — کاوه‌نگار
# ──────────────────────────────────────────────────────────────
# KAVENEGAR_API_KEY = os.environ.get('KAVENEGAR_API_KEY', '')
KAVENEGAR_API_KEY = "6D4B7557415A7974556D37755977535830755A72476250327035484E674147634C586F376F544B56684E343D"
OTP_EXPIRY_MINUTES = 5

# ──────────────────────────────────────────────────────────────
# ZARINPAL — درگاه پرداخت
# ──────────────────────────────────────────────────────────────
ZARINPAL_MERCHANT_ID = os.environ.get('ZARINPAL_MERCHANT_ID', '')
ZARINPAL_SANDBOX = True  # در محیط production روی False تنظیم شود

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
