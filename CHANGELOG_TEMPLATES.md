# گزارش تغییرات ساختار Templates

## تاریخ: ۱۴۰۳/۰۸/۰۸

### خلاصه تغییرات
پروژه به سیستم Template Inheritance یکپارچه تبدیل شد. همه صفحات حالا از یک header و footer مشترک استفاده می‌کنند.

---

## ✅ تغییرات اعمال شده

### 1️⃣ بهینه‌سازی base.html
- `base.html` آپدیت شد تا از `includes/header.html` و `includes/footer.html` استفاده کنه
- قبلاً: `{% include "header.html" %}`
- بعد: `{% include "includes/header.html" %}`

### 2️⃣ حذف فایل‌های تکراری
فایل‌های زیر در ریشه templates با پیام deprecation جایگزین شدند:
- ❌ `templates/header.html` → استفاده نشود، از `includes/header.html` استفاده کنید
- ❌ `templates/footer.html` → استفاده نشود، از `includes/footer.html` استفاده کنید

**توصیه:** این دو فایل رو می‌توانید حذف کنید:
```bash
rm templates/header.html templates/footer.html
```

### 3️⃣ حذف Header های سفارشی
فایل‌های زیر header سفارشی خودشان را داشتند که حذف شدند:

| فایل | وضعیت قبل | وضعیت بعد |
|------|-----------|-----------|
| `profile.html` | header سفارشی داشبورد | ✅ از header مشترک استفاده می‌کند |
| `login.html` | header ساده برای ورود | ✅ از header مشترک استفاده می‌کند |
| `register.html` | header ساده برای ثبت‌نام | ✅ از header مشترک استفاده می‌کند |
| `detail_course.html` | header مشابه اصلی اما جدا | ✅ از header مشترک استفاده می‌کند |
| `list_course.html` | header مشابه اصلی اما جدا | ✅ از header مشترک استفاده می‌کند |
| `detail_blog.html` | header مشابه اصلی اما جدا | ✅ از header مشترک استفاده می‌کند |
| `chapter_detail.html` | header ساده متفاوت | ✅ از header مشترک استفاده می‌کند |
| `home.html` | header مشابه اصلی اما جدا | ✅ از header مشترک استفاده می‌کند |

### 4️⃣ فایل‌هایی که Header خالی دارند
این فایل‌ها از قبل `{% block header %}{% endblock %}` خالی داشتند (صحیح بودند):
- cart.html
- checkout.html
- otp.html
- quiz.html
- quiz_list.html
- ticket_create.html
- ticket_detail.html
- payment_success.html
- payment_failed.html
- lesson_detail.html
- project.html

---

## 📊 آمار نهایی

- **تعداد کل فایل‌های HTML:** 28 فایل
- **فایل‌هایی که از base.html ارث‌بری می‌کنند:** 22 فایل
- **فایل‌هایی که اصلاح شدند:** 10 فایل
- **header های سفارشی حذف شده:** 8 مورد

---

## 🎯 نتیجه

### قبل از تغییرات:
```
❌ هر صفحه header خودش را داشت
❌ تکرار کد زیاد
❌ مدیریت سخت تغییرات
❌ ناهماهنگی در طراحی
```

### بعد از تغییرات:
```
✅ یک header مشترک برای همه صفحات
✅ تغییرات در یک جا اعمال می‌شود
✅ نگهداری آسان‌تر
✅ ظاهر یکپارچه در تمام سایت
```

---

## 📁 ساختار نهایی

```
templates/
├── base.html                 ← قالب پایه
├── includes/
│   ├── header.html          ← هدر مشترک (استفاده می‌شود) ✅
│   └── footer.html          ← فوتر مشترک (استفاده می‌شود) ✅
├── header.html              ← قدیمی (حذف شود) ❌
├── footer.html              ← قدیمی (حذف شود) ❌
├── home.html                ← از base ارث‌بری می‌کند
├── login.html               ← از base ارث‌بری می‌کند
├── profile.html             ← از base ارث‌بری می‌کند
├── detail_course.html       ← از base ارث‌بری می‌کند
└── ... (22 فایل دیگر)
```

---

## 🔧 نحوه استفاده برای صفحات جدید

```django
{% extends "base.html" %}

{% block title %}عنوان صفحه{% endblock %}

{% block content %}
<main class="pt-[148px]">
  <!-- محتوای صفحه -->
</main>
{% endblock %}
```

**نکته مهم:** از `pt-[148px]` برای فاصله از header ثابت استفاده کنید.

---

## 📝 مستندات

فایل [README.md](./README.md) در پوشه templates راهنمای کامل استفاده از این ساختار را دارد.

---

## ⚠️ نکات مهم

1. **هرگز header را در فایل‌های جدید override نکنید** مگر اینکه واقعاً نیاز باشد
2. اگر نیاز به header متفاوت دارید، ابتدا با تیم مشورت کنید
3. برای صفحات بدون header (مثل صفحات اتانتیکیشن)، از `{% block header %}{% endblock %}` استفاده کنید
4. همیشه از `{% extends "base.html" %}` در اول فایل استفاده کنید

---

تهیه شده توسط: Kiro (Claude AI Assistant)  
تاریخ: ۱۴۰۳/۰۸/۰۸
