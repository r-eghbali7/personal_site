"""Create repeatable sample data for checking the site's user-facing flows."""

import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django

django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from blog.models import BlogPost, Comment
from courses.models import (
    Category,
    Chapter,
    Choice,
    Course,
    Enrollment,
    FinalProject,
    Lesson,
    Question,
    Quiz,
)
from orders.models import Cart, CartItem, Order, OrderItem, Transaction
from tickets.models import Ticket, TicketMessage

User = get_user_model()

DEMO_VIDEO_URLS = (
    'https://www.youtube.com/watch?v=M7lc1UVf-VE',
    'https://www.youtube.com/watch?v=ScMzIvxBSi4',
    'https://www.youtube.com/watch?v=ysz5S6PUM-U',
)

COURSES = [
    {
        'slug': 'django-advanced',
        'title': 'دوره جنگو پیشرفته',
        'short_description': 'ساخت API امن و قابل توسعه با Django و Django REST Framework',
        'description': (
            'در این دوره یک سرویس واقعی را مرحله‌به‌مرحله طراحی می‌کنیم: از مدل‌سازی و '
            'اعتبارسنجی تا احراز هویت، تست‌نویسی و استقرار. هر بخش این صفحه برای همین دوره '
            'نوشته شده و محتوای آن از اطلاعات دوره در دیتابیس می‌آید.'
        ),
        'price': 1500000,
        'level': 'advanced',
        'category_slug': 'web-dev',
        'learning_outcomes': [
            'طراحی API با Django REST Framework',
            'مدیریت دسترسی و احراز هویت امن',
            'نوشتن تست برای endpointها و مدل‌ها',
            'بهینه‌سازی queryها و رفع N+1',
        ],
        'landing_sections': [
            {
                'title': 'پیش‌نیازهای جنگو پیشرفته',
                'body': 'آشنایی با Python، مدل‌های Django و کار با درخواست‌های HTTP.',
                'items': ['Python مقدماتی', 'آشنایی اولیه با Django', 'مبانی Git'],
            },
            {
                'title': 'پروژه این مسیر',
                'body': 'در پایان، API یک سامانه آموزشی را همراه با تست و مستندات تحویل می‌دهید.',
            },
        ],
        'final_project': {
            'title': 'ساخت API سامانه آموزشی',
            'description': 'پیاده‌سازی API دوره‌ها، ثبت‌نام‌ها، مجوزها و آزمون‌ها همراه با تست‌های خودکار.',
            'deadline_days': 30,
        },
        'chapters': [
            {
                'title': 'مقدمه و آماده‌سازی محیط',
                'description': 'آشنایی با ساختار پروژه، نصب وابستگی‌ها و اجرای اولین تست.',
                'quiz': 'مبانی محیط توسعه',
                'lessons': [
                    ('معرفی مسیر یادگیری', 95, True, DEMO_VIDEO_URLS[0]),
                    ('ساخت محیط مجازی و نصب Django', 184, True, DEMO_VIDEO_URLS[1]),
                    ('ساختار پروژه و تنظیمات اولیه', 247, True, DEMO_VIDEO_URLS[2]),
                ],
            },
            {
                'title': 'مدل‌سازی و پایگاه داده',
                'description': 'طراحی مدل‌های رابطه‌ای، constraintها و queryهای بهینه.',
                'quiz': 'مدل‌ها و queryها',
                'lessons': [
                    ('طراحی مدل دوره و ثبت‌نام', 612, False, DEMO_VIDEO_URLS[0]),
                    ('بهینه‌سازی queryset با select_related', 735, False, DEMO_VIDEO_URLS[1]),
                ],
            },
            {
                'title': 'ساخت API و کنترل دسترسی',
                'description': 'ساخت endpointهای خواندن و نوشتن با مجوزهای متناسب با نقش کاربر.',
                'quiz': 'API و مجوزها',
                'lessons': [
                    ('ساخت serializer و endpoint فهرست', 845, False, DEMO_VIDEO_URLS[2]),
                    ('احراز هویت و مجوزهای سفارشی', 923, False, DEMO_VIDEO_URLS[0]),
                ],
            },
        ],
    },
    {
        'slug': 'python-foundations',
        'title': 'پایتون از پایه تا پروژه',
        'short_description': 'شروع برنامه‌نویسی با تمرین‌های کوتاه و پروژه‌های کاربردی',
        'description': 'مسیر مقدماتی پایتون با مثال‌های مستقل، تمرین و یک پروژه پایانی کوچک.',
        'price': 0,
        'level': 'beginner',
        'category_slug': 'web-dev',
        'learning_outcomes': [
            'نوشتن برنامه با متغیرها و شرط‌ها',
            'کار با لیست، دیکشنری و تابع',
            'خواندن و نوشتن فایل‌های ساده',
        ],
        'landing_sections': [
            {
                'title': 'برای شروع چه لازم است؟',
                'body': 'فقط یک رایانه و آمادگی برای حل تمرین‌های کوتاه؛ تجربه برنامه‌نویسی لازم نیست.',
            },
        ],
        'final_project': {
            'title': 'مدیریت فهرست کارها با پایتون',
            'description': 'یک برنامه خط فرمان برای افزودن، نمایش و تکمیل کارها بسازید.',
            'deadline_days': 14,
        },
        'chapters': [
            {
                'title': 'شروع کار با پایتون',
                'description': 'نصب پایتون، اجرای برنامه و شناخت نوع داده‌های پایه.',
                'quiz': 'شروع پایتون',
                'lessons': [
                    ('نصب و اجرای نخستین برنامه', 305, True, DEMO_VIDEO_URLS[0]),
                    ('متغیرها و نوع داده‌ها', 428, True, DEMO_VIDEO_URLS[1]),
                ],
            },
            {
                'title': 'شرط، حلقه و تابع',
                'description': 'ساخت منطق برنامه با شرط‌ها، حلقه‌ها و توابع قابل استفاده مجدد.',
                'quiz': 'کنترل جریان برنامه',
                'lessons': [
                    ('شرط‌ها و مقایسه', 535, True, DEMO_VIDEO_URLS[2]),
                    ('حلقه‌ها و تابع‌ها', 692, True, DEMO_VIDEO_URLS[0]),
                ],
            },
        ],
    },
    {
        'slug': 'ai-api-workshop',
        'title': 'کارگاه ساخت API هوش مصنوعی',
        'short_description': 'طراحی سرویس پایتونی برای کار با مدل‌های زبانی و داده',
        'description': 'یک کارگاه پروژه‌محور برای ساخت سرویس API، مدیریت ورودی و ثبت نتیجه‌ها.',
        'price': 890000,
        'level': 'intermediate',
        'category_slug': 'ai',
        'learning_outcomes': [
            'ساخت endpoint برای پردازش متن',
            'اعتبارسنجی داده ورودی و مدیریت خطا',
            'ثبت و مشاهده تاریخچه درخواست‌ها',
        ],
        'landing_sections': [
            {
                'title': 'خروجی کارگاه',
                'body': 'در پایان، یک سرویس قابل اجرا با مستندات API و مدیریت خطا خواهید داشت.',
            },
            {
                'title': 'مخاطب این کارگاه',
                'body': 'برای برنامه‌نویسانی که با مبانی Python آشنا هستند.',
                'items': ['آشنایی با Python', 'مبانی JSON و HTTP'],
            },
        ],
        'final_project': {
            'title': 'سرویس تحلیل متن',
            'description': 'APIای بسازید که متن را دریافت کند، نتیجه را اعتبارسنجی و در تاریخچه ذخیره کند.',
            'deadline_days': 21,
        },
        'chapters': [
            {
                'title': 'مبانی سرویس‌های هوشمند',
                'description': 'معماری درخواست و پاسخ و آماده‌سازی ساختار سرویس.',
                'quiz': 'مبانی API هوشمند',
                'lessons': [
                    ('نمای کلی معماری سرویس', 372, True, DEMO_VIDEO_URLS[1]),
                    ('ساخت endpoint پردازش متن', 648, False, DEMO_VIDEO_URLS[2]),
                ],
            },
            {
                'title': 'اعتبارسنجی و ذخیره نتیجه',
                'description': 'اعتبارسنجی ورودی، ثبت خروجی و رسیدگی به خطاهای سرویس.',
                'quiz': 'اعتبارسنجی و خطاها',
                'lessons': [
                    ('اعتبارسنجی ورودی API', 560, False, DEMO_VIDEO_URLS[0]),
                    ('ثبت تاریخچه درخواست‌ها', 715, False, DEMO_VIDEO_URLS[1]),
                ],
            },
        ],
    },
]

DEMO_BLOG_ARTICLES = [
    {
        'slug': 'demo-react-components',
        'title': 'کامپوننت‌های قابل استفاده مجدد در React',
        'summary': 'چطور کامپوننت‌های کوچک و مستقل، نگهداری رابط کاربری را ساده می‌کنند؟',
        'content': 'هر کامپوننت را روی یک مسئولیت مشخص متمرکز کنید. ورودی‌های روشن و ترکیب کامپوننت‌ها، تغییر و تست رابط را آسان‌تر می‌کند.',
        'category': 'فرانت‌اند و React/Next.js',
        'tags': 'React, Frontend, Components',
        'read_time_minutes': 2,
    },
    {
        'slug': 'demo-django-api-validation',
        'title': 'اعتبارسنجی ورودی در API جنگو',
        'summary': 'اعتبارسنجی نزدیک مرز ورودی، خطاهای نامعتبر را زود و روشن مشخص می‌کند.',
        'content': 'دادهٔ ورودی را پیش از ذخیره‌سازی اعتبارسنجی کنید و برای هر خطا پاسخ قابل‌فهم بدهید. این کار از ورود دادهٔ ناسازگار به لایه‌های بعدی جلوگیری می‌کند.',
        'category': 'بک‌اند و سیستم‌های توزیع‌شده',
        'tags': 'Django, API, Validation',
        'read_time_minutes': 2,
    },
    {
        'slug': 'demo-database-indexes',
        'title': 'ایندکس پایگاه داده چه زمانی مفید است؟',
        'summary': 'ایندکس مناسب جست‌وجو را سریع‌تر می‌کند، اما هزینهٔ نوشتن و فضا هم دارد.',
        'content': 'ابتدا queryهای پرتکرار و برنامهٔ اجرای آن‌ها را بررسی کنید. سپس فقط برای ستون‌هایی که واقعاً در فیلتر یا مرتب‌سازی استفاده می‌شوند ایندکس بسازید.',
        'category': 'دیتابیس و بهینه‌سازی کوئری',
        'tags': 'Database, SQL, Index',
        'read_time_minutes': 2,
    },
    {
        'slug': 'demo-llm-prompt-basics',
        'title': 'یک الگوی ساده برای درخواست از مدل زبانی',
        'summary': 'نقش، زمینه و قالب خروجی را مشخص کنید تا پاسخ قابل پیش‌بینی‌تر باشد.',
        'content': 'درخواست خوب هدف را روشن می‌کند، اطلاعات لازم را می‌دهد و قالب خروجی را محدود می‌سازد. برای کارهای مهم، پاسخ را با دادهٔ آزمایشی ارزیابی کنید.',
        'category': 'مهندسی هوش مصنوعی و LLM',
        'tags': 'AI, LLM, Prompt',
        'read_time_minutes': 2,
    },
    {
        'slug': 'demo-docker-healthcheck',
        'title': 'Health check ساده برای سرویس کانتینری',
        'summary': 'سلامت سرویس را با یک بررسی سبک و قابل تکرار بسنجید.',
        'content': 'یک endpoint سلامت تعریف کنید که وضعیت وابستگی‌های ضروری را گزارش کند. ابزار اجرای کانتینر می‌تواند از این پاسخ برای تشخیص سرویس ناسالم استفاده کند.',
        'category': 'DevOps و Clean Architecture',
        'tags': 'Docker, DevOps, Healthcheck',
        'read_time_minutes': 2,
    },
]


def seed_course(data, instructor):
    category = Category.objects.get(slug=data['category_slug'])
    course, _ = Course.objects.update_or_create(
        slug=data['slug'],
        defaults={
            'title': data['title'],
            'short_description': data['short_description'],
            'description': data['description'],
            'learning_outcomes': data['learning_outcomes'],
            'landing_sections': data['landing_sections'],
            'price': data['price'],
            'level': data['level'],
            'is_published': True,
            'category': category,
            'instructor': instructor,
        },
    )

    for chapter_order, chapter_data in enumerate(data['chapters'], start=1):
        chapter, _ = Chapter.objects.update_or_create(
            course=course,
            order=chapter_order,
            defaults={
                'title': chapter_data['title'],
                'description': chapter_data['description'],
            },
        )
        for lesson_order, lesson_data in enumerate(chapter_data['lessons'], start=1):
            title, duration, is_preview, video_url = lesson_data
            Lesson.objects.update_or_create(
                chapter=chapter,
                order=lesson_order,
                defaults={
                    'title': title,
                    'duration_seconds': duration,
                    'is_free_preview': is_preview,
                    'video_url': video_url,
                },
            )

        quiz, _ = Quiz.objects.update_or_create(
            chapter=chapter,
            defaults={'title': chapter_data['quiz'], 'pass_score': 70},
        )
        question, _ = Question.objects.update_or_create(
            quiz=quiz,
            order=1,
            defaults={'body': f'مهم‌ترین هدف فصل «{chapter.title}» چیست؟'},
        )
        Choice.objects.update_or_create(
            question=question,
            text='تمرین و پیاده‌سازی مفاهیم همین فصل',
            defaults={'is_correct': True},
        )
        Choice.objects.update_or_create(
            question=question,
            text='نادیده گرفتن ساختار پروژه',
            defaults={'is_correct': False},
        )

    FinalProject.objects.update_or_create(course=course, defaults=data['final_project'])
    return course


@transaction.atomic
def main():
    admin, _ = User.objects.update_or_create(
        phone_number='09120000000',
        defaults={
            'full_name': 'ادمین سیستم',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        },
    )
    admin.set_password('admin1234')
    admin.save(update_fields=['password'])

    student, _ = User.objects.update_or_create(
        phone_number='09123456789',
        defaults={'full_name': 'دانشجوی نمونه', 'is_active': True},
    )
    student.set_password('student1234')
    student.save(update_fields=['password'])

    instructor, _ = User.objects.update_or_create(
        phone_number='09129876543',
        defaults={
            'full_name': 'مدرس نمونه',
            'bio': 'مدرس دوره‌های برنامه‌نویسی با تمرکز بر پروژه‌های واقعی و تست‌پذیر.',
            'is_active': True,
        },
    )
    instructor.set_password('teacher1234')
    instructor.save(update_fields=['password'])

    Category.objects.update_or_create(
        slug='web-dev',
        defaults={'name': 'برنامه‌نویسی وب', 'icon': 'code'},
    )
    Category.objects.update_or_create(
        slug='ai',
        defaults={'name': 'هوش مصنوعی', 'icon': 'psychology'},
    )

    courses = {data['slug']: seed_course(data, instructor) for data in COURSES}
    main_course = courses['django-advanced']
    free_course = courses['python-foundations']

    Enrollment.objects.update_or_create(
        user=student,
        course=main_course,
        defaults={'is_active': True},
    )
    Enrollment.objects.update_or_create(
        user=student,
        course=free_course,
        defaults={'is_active': True},
    )

    post, _ = BlogPost.objects.update_or_create(
        slug='sample-post',
        defaults={
            'title': 'راهنمای طراحی API با Django REST Framework',
            'summary': 'چند نکته کاربردی برای ساخت API قابل نگهداری در Django.',
            'content': 'در این مقاله درباره serializer، مجوزها و تست endpointهای Django صحبت می‌کنیم.',
            'author': instructor,
            'category': 'بک‌اند',
            'tags': 'Django, API, Python',
            'architecture_quiz_title': 'میزان تسلط شما به معماری نرم‌افزار چقدر است؟',
            'architecture_quiz_description': 'یک آزمون کوتاه برای سنجش درک شما از طراحی API، پیام‌رسان‌ها و الگوهای قابلیت اطمینان.',
            'podcast_title': 'شکست‌های واقعی در کلاسترهای پیام‌رسان',
            'podcast_description': 'گفت‌وگو درباره انتخاب میان Kafka و RabbitMQ در سامانه‌های پرترافیک.',
            'podcast_audio_url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
            'podcast_duration_minutes': 18,
            'coupon_discount_percent': 15,
            'read_time_minutes': 6,
            'is_published': True,
            'published_at': timezone.now(),
        },
    )
    Comment.objects.update_or_create(
        post=post,
        user=student,
        defaults={'body': 'مقاله کاربردی و قابل استفاده بود.', 'is_approved': True},
    )

    for article in DEMO_BLOG_ARTICLES:
        article_data = {
            **article,
            'author': instructor,
            'is_published': True,
            'published_at': timezone.now(),
        }
        BlogPost.objects.update_or_create(
            slug=article['slug'],
            defaults=article_data,
        )

    ticket, _ = Ticket.objects.update_or_create(
        user=student,
        subject='پرسش درباره ویدئوهای دوره',
        defaults={'status': 'open', 'priority': 'medium', 'course': main_course},
    )
    TicketMessage.objects.get_or_create(
        ticket=ticket,
        sender=student,
        body='سلام، برای دیدن فصل‌های بعدی باید وارد حساب کاربری شوم؟',
    )
    TicketMessage.objects.get_or_create(
        ticket=ticket,
        sender=instructor,
        body='سلام، پیش‌نمایش‌های رایگان بدون ورود در دسترس هستند و سایر ویدئوها بعد از ثبت‌نام پخش می‌شوند.',
    )

    order, _ = Order.objects.update_or_create(
        user=student,
        total_amount=main_course.price,
        defaults={'status': 'paid'},
    )
    OrderItem.objects.update_or_create(
        order=order,
        course=main_course,
        defaults={'price': main_course.price},
    )
    Transaction.objects.update_or_create(
        authority='AUTH-SEED-COURSE-001',
        defaults={
            'order': order,
            'status': 'success',
            'amount': int(main_course.price) * 10,
            'ref_id': 'SEED-REF-001',
        },
    )

    cart, _ = Cart.objects.get_or_create(user=student)
    CartItem.objects.update_or_create(
        cart=cart,
        course=courses['ai-api-workshop'],
        defaults={'price_snapshot': courses['ai-api-workshop'].price},
    )

    print('Seed complete: 3 courses, 7 chapters, sample lessons/videos, quizzes, project, enrollment, blog, ticket, order, and cart item.')
    print('Demo accounts: admin 09120000000 / admin1234, student 09123456789 / student1234, instructor 09129876543 / teacher1234')
    print('Course pages: /courses/django-advanced/, /courses/python-foundations/, /courses/ai-api-workshop/')


if __name__ == '__main__':
    main()
