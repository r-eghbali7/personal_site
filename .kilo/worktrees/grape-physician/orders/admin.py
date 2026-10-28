"""
Admin: orders
"""

from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, Transaction


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('price_snapshot', 'added_at')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'get_items_count', 'get_total', 'created_at')
    inlines = [CartItemInline]
    readonly_fields = ('created_at',)

    @admin.display(description='تعداد آیتم')
    def get_items_count(self, obj):
        return obj.get_items_count()

    @admin.display(description='جمع کل')
    def get_total(self, obj):
        return f'{obj.get_total():,} تومان'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('course', 'price')


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ('authority', 'ref_id', 'status', 'amount', 'created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__phone_number', 'user__full_name')
    list_editable = ('status',)
    inlines = [OrderItemInline, TransactionInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'order', 'authority', 'ref_id', 'status', 'amount', 'created_at')
    list_filter = ('status',)
    search_fields = ('authority', 'ref_id')
    readonly_fields = ('created_at', 'updated_at')
