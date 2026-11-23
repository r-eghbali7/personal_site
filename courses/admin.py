"""
Admin: courses — پنل مدیریت یکپارچهٔ دوره‌ها

هدف چیدمان این فایل: تعریف کامل یک دوره در یک صفحه انجام شود؛
اطلاعات پایه، دسته‌بندی (با امکان ساخت سریع دسته‌بندی جدید)، مدرس،
قیمت، رسانه، محتوای صفحه، فصل‌ها و پروژهٔ نهایی همه در فرم خود دوره هستند.
"""

from django import forms
from django.contrib import admin
from django.db.models import Count
from django.utils.text import slugify

from .models import (
    Category, Course, CourseFAQ, Chapter, Lesson, CourseComment, Enrollment,
    Quiz, Question, Choice, QuizAttempt, FinalProject, ProjectSubmission
)


# ──────────────────────────────────────────────────────────────
# فرم دوره: انتخاب دسته‌بندی یا ساخت دسته‌بندی جدید در همان صفحه
# ──────────────────────────────────────────────────────────────

class CourseAdminForm(forms.ModelForm):
    new_category_name = forms.CharField(
        label='یا دسته‌بندی جدید بسازید',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'مثلاً: هوش مصنوعی'}),
        help_text='اگر موضوع دوره در فهرست بالا نیست، نامش را اینجا بنویسید؛ '
                  'هنگام ذخیره ساخته و برای همین دوره انتخاب می‌شود.',
    )
    new_category_icon = forms.CharField(
        label='آیکون دسته‌بندی جدید',
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'مثلاً: code'}),
        help_text='نام آیکون از Material Symbols (اختیاری).',
    )

    class Meta:
        model = Course
        fields = '__all__'

    def save(self, commit=True):
        course = super().save(commit=False)
        name = (self.cleaned_data.get('new_category_name') or '').strip()
        if name:
            icon = (self.cleaned_data.get('new_category_icon') or '').strip()
            category, created = Category.objects.get_or_create(
                slug=slugify(name, allow_unicode=True),
                defaults={'name': name, 'icon': icon},
            )
            if not created and icon and not category.icon:
                category.icon = icon
                category.save(update_fields=['icon'])
            course.category = category
            self.cleaned_data['category'] = category
        if commit:
            course.save()
            self.save_m2m()
        return course


# ──────────────────────────────────────────────────────────────
# دسته‌بندی‌ها
# ──────────────────────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'course_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(course_total=Count('courses'))

    @admin.display(description='تعداد دوره', ordering='course_total')
    def course_count(self, obj):
        return obj.course_total


# ──────────────────────────────────────────────────────────────
# دوره
# ──────────────────────────────────────────────────────────────

class ChapterInline(admin.TabularInline):
    """فصل‌های دوره، مستقیماً روی همان صفحهٔ دوره."""

    model = Chapter
    extra = 1
    fields = ('title', 'order')
    ordering = ('order',)
    show_change_link = True
    verbose_name = 'فصل'
    verbose_name_plural = 'فصل‌های دوره (برای جلسات و آزمون، روی «تغییر» همان فصل بزنید)'


class CourseFAQInline(admin.TabularInline):
    """سؤالات متداول دوره، روی همان صفحهٔ دوره."""

    model = CourseFAQ
    extra = 1
    fields = ('question', 'answer', 'order', 'is_published')
    ordering = ('order', 'id')
    verbose_name = 'سؤال متداول'
    verbose_name_plural = 'سؤالات متداول دانشجویان (همین‌جا ثبت کنید)'


class FinalProjectInline(admin.StackedInline):
    """پروژهٔ نهایی دوره، روی همان صفحهٔ دوره."""

    model = FinalProject
    extra = 0
    max_num = 1
    can_delete = False
    classes = ('collapse',)
    fields = ('title', 'description', 'deadline_days', 'sample_file')
    verbose_name = 'پروژهٔ نهایی'
    verbose_name_plural = 'پروژهٔ نهایی دوره'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm
    save_on_top = True
    list_per_page = 25
    date_hierarchy = 'created_at'

    list_display = (
        'title', 'category', 'instructor', 'price_display', 'level',
        'chapter_count', 'lesson_count', 'is_published', 'created_at',
    )
    list_display_links = ('title',)
    list_editable = ('is_published',)
    list_filter = ('is_published', 'level', 'category')
    search_fields = ('title', 'instructor__phone_number', 'instructor__full_name')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('category', 'instructor')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ChapterInline, CourseFAQInline, FinalProjectInline]
    actions = ['make_published', 'make_unpublished']

    fieldsets = (
        ('۱. اطلاعات اصلی', {
            'description': 'عنوان دوره و متنی که در فهرست دوره‌ها و صفحهٔ دوره دیده می‌شود.',
            'fields': ('title', 'slug', 'short_description', 'description'),
        }),
        ('۲. موضوع، دسته‌بندی و مدرس', {
            'description': 'موضوع دوره را انتخاب کنید؛ اگر در فهرست نیست، در دو کادر پایین نامش را بسازید. '
                           'سطح، زبان و برچسب‌ها هم همین‌جا تنظیم می‌شوند.',
            'fields': (
                'category', 'new_category_name', 'new_category_icon',
                'instructor', 'level', 'level_description', 'language', 'detail_badge',
            ),
        }),
        ('۳. قیمت، تخفیف و وضعیت انتشار', {
            'description': 'قیمت اصلی را وارد کنید. اگر تخفیف دارید، درصد و عنوان آن را بنویسید؛ '
                           'مبلغ قابل پرداخت خودکار محاسبه و در صفحهٔ دوره نمایش داده می‌شود. '
                           'قیمت صفر یعنی دوره رایگان است. تا «منتشر شده» تیک نخورد، دوره در سایت نمایش داده نمی‌شود.',
            'fields': ('price', 'discount_percent', 'discount_title', 'is_published'),
        }),
        ('۴. تصویر و ویدیوی معرفی', {
            'fields': ('thumbnail', 'intro_video'),
        }),
        ('۵. محتوای صفحهٔ دوره', {
            'classes': ('collapse',),
            'description': 'این بخش‌ها در صفحهٔ عمومی دوره نمایش داده می‌شوند و اختیاری هستند.',
            'fields': (
                'learning_outcomes', 'landing_sections', 'included_features',
                'prerequisites', 'access_details', 'project_focus',
                'enterprise_project_count',
            ),
        }),
        ('۶. زمان‌ها', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('category', 'instructor')
            .annotate(
                chapter_total=Count('chapters', distinct=True),
                lesson_total=Count('chapters__lessons', distinct=True),
            )
        )

    @admin.display(description='قیمت (تومان)', ordering='price')
    def price_display(self, obj):
        if obj.is_free:
            return 'رایگان'
        if obj.has_discount:
            return f'{obj.final_price:,} (٪{obj.discount_percent} تخفیف)'
        return f'{obj.price:,}'

    @admin.display(description='فصل', ordering='chapter_total')
    def chapter_count(self, obj):
        return obj.chapter_total

    @admin.display(description='جلسه', ordering='lesson_total')
    def lesson_count(self, obj):
        return obj.lesson_total

    @admin.action(description='انتشار دوره‌های انتخاب‌شده')
    def make_published(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} دوره منتشر شد.')

    @admin.action(description='لغو انتشار دوره‌های انتخاب‌شده')
    def make_unpublished(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'انتشار {updated} دوره لغو شد.')


# ──────────────────────────────────────────────────────────────
# فصل، جلسه، آزمون
# ──────────────────────────────────────────────────────────────

class LessonInline(admin.TabularInline):
    """جلسات فصل، در همان صفحهٔ فصل."""

    model = Lesson
    extra = 1
    fields = (
        'title', 'order', 'duration_seconds', 'is_free_preview',
        'video_file', 'video_url', 'attachment',
    )
    ordering = ('order',)


class QuizInline(admin.TabularInline):
    model = Quiz
    extra = 0
    max_num = 1
    fields = ('title', 'pass_score')
    show_change_link = True
    verbose_name = 'آزمون'
    verbose_name_plural = 'آزمون پایان فصل (برای سؤالات روی «تغییر» آزمون بزنید)'


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'lesson_count', 'has_quiz')
    list_filter = ('course__category',)
    search_fields = ('title', 'course__title')
    autocomplete_fields = ('course',)
    ordering = ('course', 'order')
    inlines = [LessonInline, QuizInline]

    fieldsets = (
        ('اطلاعات فصل', {'fields': ('course', 'title', 'order')}),
        ('توضیحات', {'fields': ('description',)}),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('course')
            .annotate(lesson_total=Count('lessons', distinct=True))
        )

    @admin.display(description='جلسه', ordering='lesson_total')
    def lesson_count(self, obj):
        return obj.lesson_total

    @admin.display(description='آزمون', boolean=True)
    def has_quiz(self, obj):
        return hasattr(obj, 'quiz')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'chapter', 'course_title', 'order',
        'duration_display', 'is_free_preview',
    )
    list_editable = ('is_free_preview',)
    list_filter = ('is_free_preview', 'chapter__course')
    search_fields = ('title', 'chapter__title', 'chapter__course__title')
    autocomplete_fields = ('chapter',)
    list_select_related = ('chapter', 'chapter__course')
    actions = ['make_free_preview', 'remove_free_preview']

    fieldsets = (
        ('جلسه', {'fields': ('chapter', 'title', 'order')}),
        ('ویدیو', {
            'description': 'یکی از دو مورد را پر کنید؛ اگر فایل آپلود شود، لینک نادیده گرفته می‌شود.',
            'fields': ('video_file', 'video_url', 'duration_seconds'),
        }),
        ('دسترسی و پیوست', {'fields': ('is_free_preview', 'attachment')}),
    )

    @admin.display(description='دوره', ordering='chapter__course__title')
    def course_title(self, obj):
        return obj.chapter.course.title

    @admin.display(description='مدت زمان', ordering='duration_seconds')
    def duration_display(self, obj):
        minutes, seconds = divmod(obj.duration_seconds, 60)
        return f'{minutes}:{seconds:02d}'

    @admin.action(description='پیش‌نمایش رایگان جلسات انتخاب‌شده')
    def make_free_preview(self, request, queryset):
        updated = queryset.update(is_free_preview=True)
        self.message_user(request, f'{updated} جلسه پیش‌نمایش رایگان شد.')

    @admin.action(description='حذف پیش‌نمایش رایگان جلسات انتخاب‌شده')
    def remove_free_preview(self, request, queryset):
        updated = queryset.update(is_free_preview=False)
        self.message_user(request, f'پیش‌نمایش رایگان {updated} جلسه حذف شد.')


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    max_num = 4
    fields = ('text', 'is_correct')


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = ('body', 'order')
    ordering = ('order',)
    show_change_link = True
    verbose_name = 'سؤال'
    verbose_name_plural = 'سؤالات (گزینه‌ها: روی «تغییر» سؤال)'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'course_title', 'pass_score', 'question_count')
    search_fields = ('title', 'chapter__title', 'chapter__course__title')
    autocomplete_fields = ('chapter',)
    list_select_related = ('chapter', 'chapter__course')
    inlines = [QuestionInline]

    fieldsets = (
        ('آزمون', {'fields': ('chapter', 'title', 'pass_score')}),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('chapter', 'chapter__course')
            .annotate(question_total=Count('questions', distinct=True))
        )

    @admin.display(description='دوره', ordering='chapter__course__title')
    def course_title(self, obj):
        return obj.chapter.course.title

    @admin.display(description='تعداد سؤال', ordering='question_total')
    def question_count(self, obj):
        return obj.question_total


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('body', 'quiz', 'order', 'choice_count')
    list_filter = ('quiz',)
    search_fields = ('body', 'quiz__title')
    autocomplete_fields = ('quiz',)
    inlines = [ChoiceInline]
    ordering = ('quiz', 'order')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(choice_total=Count('choices'))

    @admin.display(description='گزینه', ordering='choice_total')
    def choice_count(self, obj):
        return obj.choice_total


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'is_passed', 'taken_at')
    list_filter = ('quiz', 'taken_at')
    search_fields = ('user__phone_number', 'user__full_name', 'quiz__title')
    autocomplete_fields = ('user', 'quiz')
    readonly_fields = ('taken_at',)
    date_hierarchy = 'taken_at'

    @admin.display(boolean=True, description='قبول شده')
    def is_passed(self, obj):
        return obj.is_passed


# ──────────────────────────────────────────────────────────────
# پروژه نهایی و پاسخ‌ها
# ──────────────────────────────────────────────────────────────

@admin.register(FinalProject)
class FinalProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'deadline_days', 'submission_count')
    search_fields = ('title', 'course__title')
    autocomplete_fields = ('course',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(submission_total=Count('submissions'))

    @admin.display(description='ارسال‌ها', ordering='submission_total')
    def submission_count(self, obj):
        return obj.submission_total


@admin.register(ProjectSubmission)
class ProjectSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'status', 'submitted_at')
    list_filter = ('status', 'submitted_at')
    list_editable = ('status',)
    search_fields = ('user__phone_number', 'user__full_name', 'project__title')
    autocomplete_fields = ('user', 'project')
    readonly_fields = ('submitted_at',)


# ──────────────────────────────────────────────────────────────
# ثبت‌نام و دیدگاه‌ها
# ──────────────────────────────────────────────────────────────

@admin.register(CourseComment)
class CourseCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    list_editable = ('is_approved',)
    search_fields = ('user__phone_number', 'user__full_name', 'body', 'course__title')
    autocomplete_fields = ('user', 'course')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(CourseFAQ)
class CourseFAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'course', 'order', 'is_published')
    list_editable = ('order', 'is_published')
    list_filter = ('is_published', 'course')
    search_fields = ('question', 'answer', 'course__title')
    autocomplete_fields = ('course',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at', 'is_active')
    list_filter = ('is_active', 'enrolled_at')
    list_editable = ('is_active',)
    search_fields = ('user__phone_number', 'user__full_name', 'course__title')
    autocomplete_fields = ('user', 'course')
    readonly_fields = ('enrolled_at',)
    date_hierarchy = 'enrolled_at'
