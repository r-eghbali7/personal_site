"""
Admin: accounts
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, OTPCode


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('phone_number', 'full_name', 'email', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('phone_number', 'full_name', 'email')
    ordering = ('-date_joined',)

    fieldsets = (
        ('اطلاعات ورود', {'fields': ('phone_number', 'password')}),
        ('اطلاعات شخصی', {'fields': ('full_name', 'email', 'avatar', 'bio')}),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌ها', {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'full_name', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
    readonly_fields = ('date_joined', 'last_login')


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'code', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used',)
    search_fields = ('phone_number',)
    readonly_fields = ('created_at', 'expires_at')
