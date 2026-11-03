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
# APPLICATIONS
# ──────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # ادیتور محتوای وبلاگ
    "ckeditor",
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
                # Context processor سفارشی برای سبد خرید
                'orders.context_processors.cart_processor',
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

# ──────────────────────────────────────────────────────────────
# CKEDITOR 5 — ادیتور محتوای وبلاگ
# ──────────────────────────────────────────────────────────────
# CKEDITOR_5_CONFIGS = {
#     'default': {
#         'language': 'fa',
#         'toolbar': {
#             'items': [
#                 'heading', '|',
#                 'bold', 'italic', 'underline', 'strikethrough', 'subscript', 'superscript', 'code', '|',
#                 'fontFamily', 'fontSize', 'fontColor', 'fontBackgroundColor', 'highlight', '|',
#                 'bulletedList', 'numberedList', 'todoList', 'outdent', 'indent', '|',
#                 'alignment', '|',
#                 'link', 'insertImage', 'imageUpload', 'mediaEmbed', 'insertTable', 'blockQuote', '|',
#                 'htmlEmbed', 'codeBlock', 'specialCharacters', 'horizontalLine', 'pageBreak', '|',
#                 'findAndReplace', 'selectAll', 'removeFormat', 'sourceEditing', '|',
#                 'undo', 'redo',
#             ],
#         'toolbar': 'full',
#         'extraPlugins': ','.join([
#             'codesnippet',
#             'html5video',
#             'pastefromgdocs',
#         ]),
    
#             'shouldNotGroupWhenFull': True,
#         },

#         'heading': {
#             'options': [
#                 {'model': 'paragraph', 'title': 'متن', 'class': 'ck-heading_paragraph'},
#                 {'model': 'heading1', 'view': 'h1', 'title': 'سرتیتر ۱', 'class': 'ck-heading_heading1'},
#                 {'model': 'heading2', 'view': 'h2', 'title': 'سرتیتر ۲', 'class': 'ck-heading_heading2'},
#                 {'model': 'heading3', 'view': 'h3', 'title': 'سرتیتر ۳', 'class': 'ck-heading_heading3'},
#                 {'model': 'heading4', 'view': 'h4', 'title': 'سرتیتر ۴', 'class': 'ck-heading_heading4'},
#                 {'model': 'heading5', 'view': 'h5', 'title': 'سرتیتر ۵', 'class': 'ck-heading_heading5'},
#                 {'model': 'heading6', 'view': 'h6', 'title': 'سرتیتر ۶', 'class': 'ck-heading_heading6'},
#             ],
#         },
#         'mediaEmbed': {
#             'previewsInData': True,
#         },
#         'htmlEmbed': {
#             'showPreviews': True,
#         },
#         'image': {
#             'toolbar': [
#                 'imageTextAlternative', 'imageStyle:alignLeft', 'imageStyle:alignRight', 
#                 'imageStyle:alignCenter', 'linkImage', '|'
#             ],
#             'styles': ['full', 'side', 'alignLeft', 'alignRight', 'alignCenter'],
#         },
#         'table': {
#             'contentToolbar': [
#                 'tableColumn', 'tableRow', 'mergeTableCells', 
#                 'tableProperties', 'tableCellProperties'
#             ],
#         },
#         'list': {
#             'properties': {
#                 'styles': True,
#                 'startIndex': True,
#                 'reversed': True,
#             }
#         },
#         # این بخش اجازه می‌دهد تگ‌های ویدیو و HTML اختصاصی توسط ادیتور حذف نشوند
#         'htmlSupport': {
#             'allow': [
#                 {'name': '/.*/', 'attributes': True, 'classes': True, 'styles': True}
#             ]
#         },

#     },
# }

# # مدل‌ها از config_name='extends' استفاده می‌کنند؛ این نام باید در دیکشنری وجود داشته باشد.
# CKEDITOR_5_CONFIGS['extends'] = CKEDITOR_5_CONFIGS['default']

# CKEDITOR_5_FILE_UPLOAD_PERMISSION = 'staff'
# CKEDITOR_5_MAX_FILE_SIZE = 50  # برای ویدیو بهتر است حجم را کمی بیشتر کنید (مثلا ۵۰ مگابایت)

CKEDITOR_UPLOAD_PATH = 'uploads/CKEditor'
CKEDITOR_IMAGE_BACKEND = "pillow"
CKEDITOR_JQUERY_URL = '//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js'
CKEDITOR_CODESNIPPET = "/static/ckeditor/ckeditor/plugins/codesnippet/lib/highlight/highlight.pack.js"
CKEDITOR_CONFIGS = {
    'default':
        {
            # 'contentsCss': [
            #     '{% static "css/site.css" %}',  # مسیر فایل CSS  که فونت‌ها رو تعریف کردید
            # ],
            'toolbar': 'full',
            'width': 'auto',
            'extraPlugins': ','.join([
                'codesnippet',
                'html5video',
                'pastefromgdocs',
                
            ]),
        },
}

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
