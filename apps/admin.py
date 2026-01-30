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




from django.contrib import admin
from .models import ExpenseCategory, Expense, ProfitLossReport
from django.utils.html import format_html

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'expense_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def expense_count(self, obj):
        return obj.expense_set.count()
    expense_count.short_description = 'No. of Expenses'

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        'date', 
        'category_display', 
        'description_short', 
        'amount_display', 
        'payment_method_display', 
        'expense_type_display',
        'created_by_display',
        'receipt_link'
    ]
    list_filter = [
        'expense_type', 
        'payment_method', 
        'date', 
        'category'
    ]
    search_fields = [
        'description', 
        'reference_number', 
        'category__name'
    ]
    list_per_page = 25
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'expense_type', 'description', 'amount', 'date')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'reference_number', 'receipt')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def category_display(self, obj):
        return obj.category.name if obj.category else '-'
    category_display.short_description = 'Category'
    category_display.admin_order_field = 'category__name'
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def amount_display(self, obj):
        return format_html('<span style="color: red; font-weight: bold;">TZS {}</span>', obj.amount)
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def payment_method_display(self, obj):
        colors = {
            'cash': 'success',
            'bank': 'info',
            'card': 'warning',
            'mobile': 'primary'
        }
        color = colors.get(obj.payment_method, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_payment_method_display()
        )
    payment_method_display.short_description = 'Payment Method'
    
    def expense_type_display(self, obj):
        colors = {
            'operational': 'primary',
            'purchase': 'info',
            'salary': 'success',
            'rent': 'warning',
            'utility': 'secondary',
            'marketing': 'danger',
            'maintenance': 'dark',
            'other': 'light'
        }
        color = colors.get(obj.expense_type, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_expense_type_display()
        )
    expense_type_display.short_description = 'Type'
    
    def created_by_display(self, obj):
        return obj.created_by.username if obj.created_by else '-'
    created_by_display.short_description = 'Created By'
    created_by_display.admin_order_field = 'created_by__username'
    
    def receipt_link(self, obj):
        if obj.receipt:
            return format_html(
                '<a href="{}" target="_blank"><i class="fas fa-file-pdf"></i> View</a>',
                obj.receipt.url
            )
        return '-'
    receipt_link.short_description = 'Receipt'
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ProfitLossReport)
class ProfitLossReportAdmin(admin.ModelAdmin):
    list_display = [
        'period_display',
        'date_range',
        'total_sales_display',
        'total_expenses_display',
        'net_profit_display',
        'profit_margin',
        'generated_by_display',
        'generated_at'
    ]
    list_filter = ['period', 'generated_at']
    search_fields = ['notes']
    readonly_fields = [
        'total_sales', 'total_purchases', 'total_expenses',
        'gross_profit', 'net_profit', 'generated_by', 'generated_at'
    ]
    list_per_page = 20
    date_hierarchy = 'start_date'
    
    def period_display(self, obj):
        colors = {
            'daily': 'primary',
            'weekly': 'info',
            'monthly': 'success',
            'quarterly': 'warning',
            'yearly': 'danger',
            'custom': 'secondary'
        }
        color = colors.get(obj.period, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_period_display()
        )
    period_display.short_description = 'Period'
    period_display.admin_order_field = 'period'
    
    def date_range(self, obj):
        return format_html(
            '{} to {}',
            obj.start_date.strftime('%d/%m/%Y'),
            obj.end_date.strftime('%d/%m/%Y')
        )
    date_range.short_description = 'Date Range'
    date_range.admin_order_field = 'start_date'
    
    def total_sales_display(self, obj):
        return format_html('<span style="color: green;">TZS {}</span>', obj.total_sales)
    total_sales_display.short_description = 'Sales'
    total_sales_display.admin_order_field = 'total_sales'
    
    def total_expenses_display(self, obj):
        return format_html('<span style="color: red;">TZS {}</span>', obj.total_expenses)
    total_expenses_display.short_description = 'Expenses'
    total_expenses_display.admin_order_field = 'total_expenses'
    
    def net_profit_display(self, obj):
        if obj.net_profit >= 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">TZS {}</span>',
                obj.net_profit
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">(TZS {})</span>',
                abs(obj.net_profit)
            )
    net_profit_display.short_description = 'Net Profit'
    net_profit_display.admin_order_field = 'net_profit'
    
    def profit_margin(self, obj):
        if obj.total_sales > 0:
            margin = (obj.net_profit / obj.total_sales) * 100
            color = 'success' if margin >= 0 else 'danger'
            return format_html(
                '<span class="badge bg-{}">{:.2f}%</span>',
                color, margin
            )
        return format_html('<span class="badge bg-secondary">0%</span>')
    profit_margin.short_description = 'Margin'
    
    def generated_by_display(self, obj):
        return obj.generated_by.username if obj.generated_by else '-'
    generated_by_display.short_description = 'Generated By'
    generated_by_display.admin_order_field = 'generated_by__username'
    
    def has_add_permission(self, request):
        # Disable adding reports from admin - they should be generated from the system
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Allow deletion of reports
        return True