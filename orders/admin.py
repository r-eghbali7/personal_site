"""
Admin: orders
"""

from django.contrib import admin

from .models import (
    Cart,
    CartItem,
    Coupon,
    CouponRedemption,
    Order,
    OrderItem,
    Transaction,
)


class CouponRedemptionInline(admin.TabularInline):
    model = CouponRedemption
    extra = 0
    can_delete = False
    readonly_fields = ('user', 'order', 'discount_amount', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'title',
        'discount_type',
        'value',
        'user',
        'course',
        'valid_from',
        'valid_until',
        'is_active',
        'used_count',
        'usage_limit',
    )
    list_filter = ('is_active', 'discount_type', 'course')
    list_editable = ('is_active',)
    search_fields = ('code', 'title', 'user__phone_number', 'user__full_name', 'course__title')
    readonly_fields = ('used_count', 'created_at', 'updated_at')
    inlines = [CouponRedemptionInline]
    fieldsets = (
        (
            'کد و مقدار تخفیف',
            {
                'fields': ('code', 'title', 'discount_type', 'value', 'max_discount', 'is_active'),
            },
        ),
        (
            'محدوده استفاده (همه موارد اختیاری)',
            {
                'fields': (
                    'user',
                    'course',
                    'valid_from',
                    'valid_until',
                    'usage_limit',
                    'per_user_limit',
                ),
                'description': (
                    'خالی گذاشتن «کاربر اختصاصی» یعنی کد همگانی برای همه کاربران؛ '
                    'خالی گذاشتن «دوره اختصاصی» یعنی کد روی همه محصولات اعمال می‌شود؛ '
                    'و خالی گذاشتن تاریخ‌ها یعنی کد بدون محدودیت زمانی است.'
                ),
            },
        ),
        (
            'آمار استفاده',
            {
                'fields': ('used_count', 'created_at', 'updated_at'),
            },
        ),
    )


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'order', 'discount_amount', 'created_at')
    list_filter = ('coupon', 'created_at')
    search_fields = ('coupon__code', 'user__phone_number')
    readonly_fields = ('coupon', 'user', 'order', 'discount_amount', 'created_at')


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
    list_display = (
        'pk',
        'user',
        'subtotal_amount',
        'discount_amount',
        'coupon',
        'total_amount',
        'status',
        'created_at',
    )
    list_filter = ('status', 'coupon', 'created_at')
    search_fields = ('user__phone_number', 'user__full_name')
    list_editable = ('status',)
    inlines = [OrderItemInline, TransactionInline]
    readonly_fields = (
        'created_at',
        'updated_at',
        'subtotal_amount',
        'discount_amount',
        'coupon',
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'order', 'authority', 'ref_id', 'status', 'amount', 'created_at')
    list_filter = ('status',)
    search_fields = ('authority', 'ref_id')
    readonly_fields = ('created_at', 'updated_at')
