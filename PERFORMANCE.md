# گزارش بهینه‌سازی و پاک‌سازی پروژه

این گزارش نتیجهٔ یک دور بررسی پرفورمنس و کدهای بلااستفاده است.

## ۱. بهینه‌سازی فرانت‌اند (بزرگ‌ترین دستاورد)

قبلاً Tailwind به‌صورت **کامپایلر سمت مرورگر** (`static/js/tailwindcss.js` با حجم ۳۹۸ کیلوبایت) در هر صفحه اجرا می‌شد و کلاس‌ها در زمان اجرا ساخته می‌شدند (هزینهٔ CPU و دانلود).

- فایل `static/css/tailwind.css` با نسخهٔ رسمی CLI ساخته شد: **۷۸ کیلوبایت** نسخهٔ minified (به‌جای ۳۹۸ کیلوبایت JS + اجرای کامپایلر).
- تنظیمات به `tailwind.config.js` منتقل و ورودی `static/css/tailwind.input.css` اضافه شد.
- `base.html` حالا فقط یک `<link rel="stylesheet">` به CSS آماده دارد.
- دو درخواست تکراری فونت Material Symbols به یک درخواست کاهش یافت.
- اسکریپت `site-header.js` که در صفحهٔ لیست مقالات **دو بار** لود می‌شد (یک بار در base و یک بار تزریق دستی در ویو) حذف شد.

### ساخت دوبارهٔ CSS

بعد از هر تغییر در کلاس‌های قالب‌ها یا فایل‌های JS، این دستور را اجرا کنید:

```bash
npx tailwindcss@3.4.17 -c tailwind.config.js -i static/css/tailwind.input.css -o static/css/tailwind.css --minify
```

> در محیط production یک‌بار `python manage.py collectstatic` هم لازم است.

## ۲. حذف فایل‌های بلااستفاده

این فایل‌ها ارجاعی نداشتند و حذف شدند:

- `static/js/tailwindcss.js`
- `static/js/tailwindcss-plugins.js`
- `static/js/tailwind-config.js`
- `static/js/l.js`
- `static/css/google-fonts.css`
- `static/css/material-symbols-outlined.css`
- `static/css/material-symbols-outlined-swap.css`
- `static/js/keen-slider.min.js` (نسخهٔ CDN استفاده می‌شود)
- `static/css/keen-slider.min.css`
- `templates/course_detail_content.html` (قالب قدیمی و بدون استفاده)

## ۳. بهینه‌سازی کوئری‌ها

تعداد کوئری دیتابیس برای صفحات اصلی (قبل ← بعد):

| صفحه | قبل | بعد |
|---|---|---|
| صفحه اصلی | ۴ | ۴ |
| لیست دوره‌ها | ۴ | ۴ |
| جزئیات دوره | ۷ | **۶** |
| لیست مقالات | ۴ | **۳** |
| صفحه پادکست‌ها | ۳ | **۲** |

- `cart_processor`: به‌جای دو کوئری (سبد + شمارش آیتم‌ها) حالا با یک `annotate(Count)` انجام می‌شود.
- `CourseDetailView`: لیست دیدگاه‌ها یک‌بار خوانده و طول آن استفاده می‌شود (بدون COUNT جدا).
- `PodcastListView`: لیست یک‌بار ارزیابی و تعداد از `len` گرفته می‌شود.
- `BlogListView`: در حالت بدون فیلتر، COUNT تکراری Paginator حذف شد.
- تصاویر کارت دوره‌های صفحه اصلی `loading="lazy"` و `decoding="async"` دارند.

## ۴. ایندکس‌های دیتابیس

مایگریشن‌های جدید برای کوئری‌های پرتکرار:

- `courses`: ایندکس ترکیبی `(is_published, -created_at)` روی دوره، و `(course, is_approved)` روی دیدگاه دوره
- `blog`: ایندکس `(is_published, -published_at)` روی مقاله، و `(post, is_approved)` روی دیدگاه مقاله و پادکست
- `orders`: ایندکس روی `Cart.session_key` و `Order.status`

## ۵. توصیه‌های باقی‌مانده برای production

1. `DJANGO_DEBUG=False` و اجرای `collectstatic`؛ سرو استاتیک با Nginx/CDN یا WhiteNoise.
2. مهاجرت از SQLite به PostgreSQL برای ترافیک واقعی.
3. میزبانی لوکال تصاویر (بسیاری از تصاویر از `lh3.googleusercontent.com` و `hosseintaheri.ir` لود می‌شوند) و تبدیل به WebP/AVIF با ابعاد مناسب.
4. در صورت افزایش ترافیک، کش صفحه اصلی/فهرست‌ها با Redis یا کش تکه‌ای (Fragment cache).
5. افزودن `width`/`height` به تصاویر برای کاهش Layout Shift.
6. فونت‌ها در صورت امکان self-host شوند تا وابستگی به Google Fonts کم شود.

## تست‌ها

- ویرایشگر محتوای مقاله و دوره با CKEditor 5 پیکربندی شده است.
- مجموعاً ۹۰ تست اجرا می‌شود و همهٔ تست‌ها موفق هستند.
