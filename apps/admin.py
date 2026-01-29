from django.contrib import admin
from django.db import models
from .models import *


# ✅ Custom filter for is_low_stock
class LowStockFilter(admin.SimpleListFilter):
    title = 'Low stock'
    parameter_name = 'is_low_stock'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Low stock'),
            ('no', 'In stock'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(quantity__lte=models.F('reorder_level'))
        if self.value() == 'no':
            return queryset.filter(quantity__gt=models.F('reorder_level'))
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'sku',
        'category',
        'quantity',
        'price',
        'is_low_stock',  # ✅ still here
    )

    list_filter = (
        'category',
        LowStockFilter,  # ✅ replaces direct field reference
        'created_at',
    )

    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'sku', 'description', 'category', 'unit', 'image')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'cost_price', 'quantity', 'reorder_level')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone')
    search_fields = ('name', 'contact_person', 'email')


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'quantity', 'created_by', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('product__name', 'reference')
    readonly_fields = ('created_at',)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer_name', 'total_amount', 'payment_method', 'created_at')
    list_filter = ('payment_method', 'created_at')
    search_fields = ('invoice_number', 'customer_name', 'customer_phone')
    readonly_fields = ('created_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'role')
    search_fields = ('user__username', 'phone')
