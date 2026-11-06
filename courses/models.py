"""
App: courses — مدل‌های دوره، فصل، جلسه، کوییز، پروژه نهایی
"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify
from ckeditor.fields import RichTextField


class Category(models.Model):
    """دسته‌بندی دوره‌ها."""

    name = models.CharField(max_length=100, verbose_name='نام دسته‌بندی')
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name='اسلاگ')
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='آیکون (Material Symbols)',
        help_text='نام آیکون از Material Symbols مثلاً: code, school',
    )

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'

    def __str__(self):
        return self.name


class Course(models.Model):
    """مدل اصلی دوره آموزشی."""

    LEVEL_CHOICES = [
        ('beginner', 'مقدماتی'),
        ('intermediate', 'متوسط'),
        ('advanced', 'پیشرفته'),
    ]

    title = models.CharField(max_length=250, verbose_name='عنوان دوره')
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name='اسلاگ')
    short_description = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='توضیح کوتاه',
    )
    description = RichTextField('توضیحات کامل', config_name='extends')
    learning_outcomes = models.JSONField(
        default=list,
        blank=True,
        verbose_name='مهارت‌های اکتسابی',
        help_text='فهرستی از مهارت‌ها به صورت JSON؛ نمونه: ["طراحی API", "تست‌نویسی"].',
    )
    landing_sections = models.JSONField(
        default=list,
        blank=True,
        verbose_name='بخش‌های اختصاصی صفحه دوره',
        help_text='فهرستی از بخش‌ها با کلیدهای title و body؛ نمونه: [{"title": "پیش‌نیازها", "body": "آشنایی با Python"}].',
    )
    thumbnail = models.ImageField(
        upload_to='courses/thumbnails/',
        blank=True,
        null=True,
        verbose_name='تصویر بندانگشتی',
    )
    intro_video = models.FileField(
        upload_to='courses/intro_videos/',
        blank=True,
        null=True,
        verbose_name='ویدیوی معرفی دوره',
        help_text='ویدیوی معرفی/پیش‌نمایش دوره که در بالای صفحه با پخش‌کننده قابل تماشاست.',
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='قیمت (تومان)',
        help_text='صفر به معنای رایگان است.',
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='beginner',
        verbose_name='سطح دوره',
    )
    detail_badge = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='برچسب صفحه جزئیات',
    )
    level_description = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='شرح سطح دوره',
    )
    project_focus = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='نوع پروژه‌های دوره',
    )
    language = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='زبان دوره',
    )
    prerequisites = models.TextField(
        blank=True,
        verbose_name='پیش‌نیازهای دوره',
    )
    access_details = models.TextField(
        blank=True,
        verbose_name='جزئیات دسترسی دوره',
    )
    included_features = models.JSONField(
        default=list,
        blank=True,
        verbose_name='موارد شامل دوره',
        help_text='فهرستی از موارد با کلیدهای icon و text.',
    )
    is_published = models.BooleanField(default=False, verbose_name='منتشر شده')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='دسته‌بندی',
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teaching_courses',
        verbose_name='مدرس',
    )
    enterprise_project_count = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد پروژه‌های انترپرایز',
        help_text='تعداد پروژه‌های جامع انترپرایز دوره (برای نمایش در بخش آمار)',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'دوره'
        verbose_name_plural = 'دوره‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', '-created_at']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_free(self):
        return self.price == 0

    def get_total_duration(self):
        """مجموع مدت زمان جلسات دوره (به ثانیه)."""
        return sum(
            lesson.duration_seconds
            for chapter in self.chapters.all()
            for lesson in chapter.lessons.all()
        )

    def is_enrolled(self, user):
        """بررسی اینکه کاربر در دوره ثبت‌نام کرده یا نه."""
        if not user.is_authenticated:
            return False
        return self.enrollments.filter(user=user, is_active=True).exists()


class Chapter(models.Model):
    """فصل/بخش دوره."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='chapters',
        verbose_name='دوره',
    )
    title = models.CharField(max_length=200, verbose_name='عنوان فصل')
    description = RichTextField('توضیحات فصل', blank=True, config_name='extends')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        verbose_name = 'فصل'
        verbose_name_plural = 'فصل‌ها'
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} — {self.title}'

    @property
    def total_duration_seconds(self):
        return sum(lesson.duration_seconds for lesson in self.lessons.all())

    @property
    def total_duration_minutes(self):
        return (self.total_duration_seconds + 59) // 60


class Lesson(models.Model):
    """جلسه/درس داخل یک فصل."""

    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='فصل',
    )
    title = models.CharField(max_length=200, verbose_name='عنوان جلسه')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    video_file = models.FileField(
        upload_to='courses/videos/',
        blank=True,
        null=True,
        verbose_name='فایل ویدیو',
    )
    video_url = models.URLField(
        blank=True,
        verbose_name='لینک ویدیو (YouTube/Aparat)',
        help_text='در صورت آپلود فایل، این فیلد نادیده گرفته می‌شود.',
    )
    attachment = models.FileField(
        upload_to='courses/attachments/',
        blank=True,
        null=True,
        verbose_name='فایل پیوست',
    )
    duration_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name='مدت زمان (ثانیه)',
    )
    is_free_preview = models.BooleanField(
        default=False,
        verbose_name='پیش‌نمایش رایگان',
        help_text='اگر فعال باشد، این جلسه برای همه کاربران قابل مشاهده است حتی اگر دوره پولی باشد.',
    )

    class Meta:
        verbose_name = 'جلسه'
        verbose_name_plural = 'جلسات'
        ordering = ['order']

    def __str__(self):
        return f'{self.chapter.title} — {self.title}'

    @property
    def duration_minutes(self):
        return (self.duration_seconds + 59) // 60

    def can_access(self, user):
        """
        بررسی دسترسی کاربر به این جلسه.
        قوانین:
          - دوره رایگان → همه می‌توانند ببینند
          - is_free_preview → همه می‌توانند ببینند
          - دوره پولی + کاربر ثبت‌نام کرده → دسترسی دارد
        """
        course = self.chapter.course
        if course.is_free:
            return True
        if self.is_free_preview:
            return True
        if user.is_authenticated and course.is_enrolled(user):
            return True
        return False


class CourseComment(models.Model):
    """دیدگاه کاربران درباره یک دوره."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='دوره',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_comments',
        verbose_name='کاربر',
    )
    body = models.TextField(verbose_name='متن دیدگاه')
    is_approved = models.BooleanField(
        default=True,
        verbose_name='تأیید شده',
        help_text='برای پنهان کردن دیدگاه از سایت، تیک آن را بردارید.',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')

    class Meta:
        verbose_name = 'دیدگاه دوره'
        verbose_name_plural = 'دیدگاه‌های دوره'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'is_approved']),
        ]

    def __str__(self):
        return f'{self.user} روی دوره {self.course_id}'


class Enrollment(models.Model):
    """ثبت‌نام کاربر در یک دوره."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='کاربر',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='دوره',
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت‌نام')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'ثبت‌نام'
        verbose_name_plural = 'ثبت‌نام‌ها'
        unique_together = ('user', 'course')

    def __str__(self):
        return f'{self.user} ← {self.course}'


# ──────────────────────────────────────────────────────────────
# سیستم آزمون (Quiz)
# ──────────────────────────────────────────────────────────────

class Quiz(models.Model):
    """آزمون پایان فصل."""

    chapter = models.OneToOneField(
        Chapter,
        on_delete=models.CASCADE,
        related_name='quiz',
        verbose_name='فصل',
    )
    title = models.CharField(max_length=200, verbose_name='عنوان آزمون')
    pass_score = models.PositiveIntegerField(
        default=70,
        verbose_name='نمره قبولی',
        help_text='از ۱۰۰',
    )

    class Meta:
        verbose_name = 'آزمون'
        verbose_name_plural = 'آزمون‌ها'

    def __str__(self):
        return self.title


class Question(models.Model):
    """سؤال چندگزینه‌ای."""

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='آزمون',
    )
    body = RichTextField(verbose_name='متن سؤال')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        verbose_name = 'سؤال'
        verbose_name_plural = 'سؤالات'
        ordering = ['order']

    def __str__(self):
        return self.body[:80]


class Choice(models.Model):
    """گزینه سؤال."""

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name='سؤال',
    )
    text = models.CharField(max_length=500, verbose_name='متن گزینه')
    is_correct = models.BooleanField(default=False, verbose_name='گزینه صحیح')

    class Meta:
        verbose_name = 'گزینه'
        verbose_name_plural = 'گزینه‌ها'

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    """نتیجه شرکت کاربر در آزمون."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name='کاربر',
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='آزمون',
    )
    score = models.PositiveIntegerField(default=0, verbose_name='نمره (از ۱۰۰)')
    taken_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ شرکت')

    class Meta:
        verbose_name = 'نتیجه آزمون'
        verbose_name_plural = 'نتایج آزمون‌ها'
        ordering = ['-taken_at']

    def __str__(self):
        return f'{self.user} — {self.quiz} — {self.score}'

    @property
    def is_passed(self):
        return self.score >= self.quiz.pass_score


# ──────────────────────────────────────────────────────────────
# پروژه نهایی دوره
# ──────────────────────────────────────────────────────────────

class FinalProject(models.Model):
    """پروژه نهایی دوره که دانشجو باید ارسال کند."""

    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name='final_project',
        verbose_name='دوره',
    )
    title = models.CharField(max_length=250, verbose_name='عنوان پروژه')
    description = RichTextField('شرح پروژه', config_name='extends')
    sample_file = models.FileField(
        upload_to='projects/samples/',
        blank=True,
        null=True,
        verbose_name='فایل نمونه',
    )
    deadline_days = models.PositiveIntegerField(
        default=30,
        verbose_name='مهلت ارسال (روز پس از ثبت‌نام)',
    )

    class Meta:
        verbose_name = 'پروژه نهایی'
        verbose_name_plural = 'پروژه‌های نهایی'

    def __str__(self):
        return f'پروژه: {self.course.title}'


class ProjectSubmission(models.Model):
    """پاسخ دانشجو به پروژه نهایی."""

    STATUS_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('reviewed', 'در حال بررسی'),
        ('accepted', 'پذیرفته شده'),
        ('rejected', 'رد شده'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_submissions',
        verbose_name='کاربر',
    )
    project = models.ForeignKey(
        FinalProject,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='پروژه',
    )
    submitted_file = models.FileField(
        upload_to='projects/submissions/',
        verbose_name='فایل ارسالی',
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات دانشجو',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت',
    )
    feedback = models.TextField(
        blank=True,
        verbose_name='بازخورد مدرس',
    )
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ارسال')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ بررسی')

    class Meta:
        verbose_name = 'پاسخ پروژه'
        verbose_name_plural = 'پاسخ‌های پروژه'
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.user} → {self.project}'
