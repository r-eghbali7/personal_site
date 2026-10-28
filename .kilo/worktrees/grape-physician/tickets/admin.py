"""
Admin: tickets
"""

from django.contrib import admin
from .models import Ticket, TicketMessage


class TicketMessageInline(admin.StackedInline):
    model = TicketMessage
    extra = 1
    readonly_fields = ('sent_at',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'subject', 'status', 'priority', 'course', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('user__phone_number', 'subject')
    list_editable = ('status', 'priority')
    inlines = [TicketMessageInline]
    readonly_fields = ('created_at', 'updated_at')
