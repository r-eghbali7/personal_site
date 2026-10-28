"""
Admin: courses
"""

from django.contrib import admin
from .models import (
    Category, Course, Chapter, Lesson, Enrollment,
    Quiz, Question, Choice, QuizAttempt, FinalProject, ProjectSubmission
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 1
    fields = ('title', 'description', 'order')


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'order', 'duration_seconds', 'is_free_preview', 'video_file', 'video_url')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'price', 'level', 'is_published', 'created_at')
    list_filter = ('is_published', 'level', 'category')
    search_fields = ('title', 'instructor__phone_number', 'instructor__full_name')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ChapterInline]
    list_editable = ('is_published',)


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'order', 'duration_seconds', 'is_free_preview')
    list_filter = ('is_free_preview', 'chapter__course')
    list_editable = ('is_free_preview',)
    search_fields = ('title',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at', 'is_active')
    list_filter = ('is_active', 'enrolled_at')
    search_fields = ('user__phone_number', 'course__title')
    list_editable = ('is_active',)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    max_num = 4


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    inlines = [ChoiceInline]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'pass_score')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('body', 'quiz', 'order')
    list_filter = ('quiz',)
    inlines = [ChoiceInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'is_passed', 'taken_at')
    list_filter = ('quiz',)
    readonly_fields = ('taken_at',)

    @admin.display(boolean=True, description='قبول شده')
    def is_passed(self, obj):
        return obj.is_passed


@admin.register(FinalProject)
class FinalProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'deadline_days')


@admin.register(ProjectSubmission)
class ProjectSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'status', 'submitted_at')
    list_filter = ('status',)
    list_editable = ('status',)
    readonly_fields = ('submitted_at',)
