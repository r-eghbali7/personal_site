"""
Admin: blog
"""

from django.contrib import admin
from .models import BlogPost, Comment


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('user', 'created_at')
    fields = ('user', 'body', 'is_approved', 'created_at')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_published', 'views_count', 'published_at')
    list_filter = ('is_published', 'category', 'published_at')
    search_fields = ('title', 'content', 'author__phone_number')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_published',)
    inlines = [CommentInline]
    readonly_fields = ('views_count', 'created_at', 'updated_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    list_editable = ('is_approved',)
    search_fields = ('user__phone_number', 'body')
