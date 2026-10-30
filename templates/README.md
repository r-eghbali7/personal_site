# ساختار Templates در پروژه

این پروژه از سیستم Template Inheritance جنگو استفاده می‌کند تا از تکرار کد جلوگیری شود.

## ساختار اصلی

### 📄 base.html
فایل پایه که تمام صفحات از آن ارث‌بری می‌کنند. شامل:
- تگ‌های HTML اصلی (html, head, body)
- تنظیمات Tailwind CSS
- فونت‌ها و آیکون‌های Material Symbols
- استایل‌های مشترک
- بلاک‌های قابل override:
  - `{% block title %}` - عنوان صفحه
  - `{% block meta %}` - متا تگ‌های اضافی
  - `{% block head %}` - CSS و اسکریپت‌های اضافی در head
  - `{% block body_class %}` - کلاس‌های اضافی برای body
  - `{% block header %}` - هدر صفحه (پیش‌فرض: includes/header.html)
  - `{% block content %}` - محتوای اصلی صفحه
  - `{% block footer %}` - فوتر صفحه (پیش‌فرض: includes/footer.html)
  - `{% block scripts %}` - اسکریپت‌های اضافی در انتهای body

### 📁 پوشه includes/
فایل‌های قابل استفاده مجدد که با `{% include %}` فراخوانی می‌شوند:

#### includes/header.html
- هدر ثابت (fixed) در بالای صفحه
- نوار اطلاعات تماس
- لوگو و نام آکادمی
- منوی ناوبری اصلی
- جستجو
- آیکون سبد خرید
- اطلاعات کاربر / دکمه ورود

#### includes/footer.html
- اطلاعات آکادمی
- لینک‌های دسترسی سریع
- فرم عضویت در خبرنامه
- نمادها و شبکه‌های اجتماعی
- کپی‌رایت

## نحوه استفاده

### ایجاد یک صفحه جدید:

```django
{% extends "base.html" %}

{% block title %}عنوان صفحه | آکادمی حسین طاهری{% endblock %}

{% block head %}
<!-- CSS اختصاصی این صفحه -->
<style>
  .custom-class { color: red; }
</style>
{% endblock %}

{% block content %}
<main class="pt-[148px] min-h-screen">
  <!-- محتوای صفحه -->
  <h1>سلام دنیا!</h1>
</main>
{% endblock %}

{% block scripts %}
<!-- JavaScript اختصاصی این صفحه -->
<script>
  console.log('صفحه بارگذاری شد');
</script>
{% endblock %}
```

### نکات مهم:

1. **همیشه از `{% extends "base.html" %}` استفاده کنید** - این خط باید اولین خط فایل باشد
2. **از padding-top مناسب استفاده کنید** - header ثابت است و ارتفاع آن حدود 148px است
3. **برای override کردن header یا footer**: می‌توانید بلاک header یا footer را در فایل خود بازنویسی کنید
4. **از `{% load static %}` استفاده کنید** اگر به فایل‌های استاتیک نیاز دارید

### مثال override کردن header:

```django
{% extends "base.html" %}

{% block header %}
<!-- header سفارشی فقط برای این صفحه -->
<header class="custom-header">
  <h1>هدر سفارشی</h1>
</header>
{% endblock %}

{% block content %}
<!-- محتوای صفحه -->
{% endblock %}
```

## فایل‌های موجود

تمام فایل‌های HTML زیر از `base.html` ارث‌بری می‌کنند:

- home.html - صفحه اصلی
- login.html - ورود
- register.html - ثبت‌نام
- otp.html - تایید کد OTP
- profile.html - پروفایل کاربر
- list_course.html - لیست دوره‌ها
- detail_course.html - جزئیات دوره
- list_blog.html - لیست مقالات
- detail_blog.html - جزئیات مقاله
- cart.html - سبد خرید
- checkout.html - تسویه‌حساب
- quiz_list.html - لیست آزمون‌ها
- quiz.html - صفحه آزمون
- ticket_list.html - لیست تیکت‌ها
- ticket_detail.html - جزئیات تیکت
- ticket_create.html - ایجاد تیکت جدید
- و...

## توجه

⚠️ فایل‌های `header.html` و `footer.html` در ریشه پوشه templates دیگر استفاده نمی‌شوند و می‌توانند حذف شوند. به جای آن‌ها از `includes/header.html` و `includes/footer.html` استفاده می‌شود.

## مزایای این ساختار

✅ حذف کدهای تکراری  
✅ مدیریت آسان‌تر تغییرات  
✅ سازگاری کامل با بهترین روش‌های جنگو  
✅ امکان سفارشی‌سازی هر صفحه در صورت نیاز  
✅ نگهداری آسان‌تر کد  

---

آخرین بروزرسانی: ۱۴۰۳/۰۸/۰۸
