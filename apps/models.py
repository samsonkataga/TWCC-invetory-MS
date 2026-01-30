from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    UNIT_CHOICES = [
        ('piece', 'Piece'),
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('pack', 'Pack'),
        ('box', 'Box'),
    ]
    
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def total_value(self):
        return self.quantity * self.cost_price
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjust', 'Adjustment'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.product.name} ({self.quantity})"

class Sale(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Bank Transfer'),
        ('credit', 'Credit'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    items = models.JSONField()  # Store sale items as JSON
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.invoice_number

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    role = models.CharField(max_length=50, default='staff')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.username



# Add these models to your existing models.py

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Expense Categories"

class Expense(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Money'),
    ]
    
    EXPENSE_TYPES = [
        ('operational', 'Operational'),
        ('purchase', 'Purchase'),
        ('salary', 'Salary'),
        ('rent', 'Rent'),
        ('utility', 'Utility'),
        ('marketing', 'Marketing'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]
    
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True)
    expense_type = models.CharField(max_length=50, choices=EXPENSE_TYPES, default='operational')
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='cash')
    reference_number = models.CharField(max_length=100, blank=True)
    date = models.DateField()
    receipt = models.FileField(upload_to='expenses/receipts/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.description} - TZS{self.amount}"
    
    class Meta:
        ordering = ['-date', '-created_at']

class ProfitLossReport(models.Model):
    REPORT_PERIODS = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]
    
    period = models.CharField(max_length=20, choices=REPORT_PERIODS)
    start_date = models.DateField()
    end_date = models.DateField()
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_purchases = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"PL Report {self.start_date} to {self.end_date}"
    
    class Meta:
        ordering = ['-start_date']