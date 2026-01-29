from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg, F
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from .forms import *
from .decorators import admin_required

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'apps/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    # Get statistics
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(quantity__lte=F('reorder_level')).count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()
    
    # User activity counts
    user_sales_count = Sale.objects.filter(created_by=request.user).count()
    user_products_count = Product.objects.filter(created_by=request.user).count()
    user_transactions_count = StockTransaction.objects.filter(created_by=request.user).count()
    
    # Today's sales
    today = timezone.now().date()
    today_sales = Sale.objects.filter(created_at__date=today).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Recent transactions
    recent_transactions = StockTransaction.objects.select_related('product', 'created_by').order_by('-created_at')[:10]
    
    # Low stock items
    low_stock_items = Product.objects.filter(quantity__lte=F('reorder_level')).order_by('quantity')[:5]
    
    # Sales chart data (last 7 days)
    sales_data = []
    dates_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        daily_sales = Sale.objects.filter(created_at__date=date).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        sales_data.append(float(daily_sales))
        dates_data.append(date.strftime('%a'))
    
    context = {
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'total_categories': total_categories,
        'total_suppliers': total_suppliers,
        'today_sales': today_sales,
        'recent_transactions': recent_transactions,
        'low_stock_items': low_stock_items,
        'sales_data': sales_data,
        'dates_data': dates_data,
        'user_sales_count': user_sales_count,
        'user_products_count': user_products_count,
        'user_transactions_count': user_transactions_count,
    }
    return render(request, 'apps/dashboard.html', context)

@login_required
@admin_required
def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('user_list')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'apps/users/create.html', {'form': form})

@login_required
@admin_required
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    
    # Calculate statistics
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    admin_users = users.filter(is_staff=True).count()
    staff_users = users.filter(is_staff=False).count()
    
    context = {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'staff_users': staff_users,
    }
    return render(request, 'apps/users/list.html', context)

@login_required
def product_list(request):
    products = Product.objects.select_related('category').all()
    form = SearchForm(request.GET or None)
    
    if form.is_valid() and form.cleaned_data['query']:
        query = form.cleaned_data['query']
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(description__icontains=query)
        )
    
    return render(request, 'apps/products/list.html', {
        'products': products,
        'form': form
    })

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('product_list')
    else:
        form = ProductForm()
    
    # Add statistics to context
    total_products = Product.objects.count()
    low_stock_count = Product.objects.filter(quantity__lte=F('reorder_level')).count()
    out_of_stock = Product.objects.filter(quantity=0).count()
    
    context = {
        'form': form,
        'title': 'Add New Product',
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock': out_of_stock,
    }
    
    return render(request, 'apps/products/form.html', context)

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    
    # Add statistics to context
    total_products = Product.objects.count()
    low_stock_count = Product.objects.filter(quantity__lte=F('reorder_level')).count()
    out_of_stock = Product.objects.filter(quantity=0).count()
    
    context = {
        'form': form,
        'title': 'Edit Product',
        'product': product,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock': out_of_stock,
    }
    
    return render(request, 'apps/products/form.html', context)

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('product_list')
    
    return render(request, 'apps/products/confirm_delete.html', {'product': product})

@login_required
def stock_in(request):
    if request.method == 'POST':
        form = StockTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.transaction_type = 'in'
            transaction.save()
            
            # Update product quantity
            product = transaction.product
            product.quantity += transaction.quantity
            product.save()
            
            messages.success(request, f'Stock added for {product.name}')
            return redirect('stock_transactions')
    else:
        form = StockTransactionForm()
        form.fields['transaction_type'].initial = 'in'
    
    # Add recent transactions to context
    recent_transactions = StockTransaction.objects.select_related('product').order_by('-created_at')[:5]
    
    context = {
        'form': form,
        'title': 'Stock In',
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'apps/stock/transaction_form.html', context)

@login_required
def stock_out(request):
    if request.method == 'POST':
        form = StockTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.transaction_type = 'out'
            
            # Check if enough stock is available
            if transaction.product.quantity >= transaction.quantity:
                transaction.save()
                product = transaction.product
                product.quantity -= transaction.quantity
                product.save()
                messages.success(request, f'Stock removed for {product.name}')
                return redirect('stock_transactions')
            else:
                messages.error(request, 'Insufficient stock available!')
    
    else:
        form = StockTransactionForm()
        form.fields['transaction_type'].initial = 'out'
    
    # Add recent transactions to context
    recent_transactions = StockTransaction.objects.select_related('product').order_by('-created_at')[:5]
    
    context = {
        'form': form,
        'title': 'Stock Out',
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'apps/stock/transaction_form.html', context)

@login_required
def stock_transactions(request):
    transactions = StockTransaction.objects.select_related('product', 'created_by').order_by('-created_at')
    
    # Filter by date if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    trans_type = request.GET.get('type')
    
    if start_date and end_date:
        transactions = transactions.filter(created_at__date__range=[start_date, end_date])
    
    if trans_type:
        transactions = transactions.filter(transaction_type=trans_type)
    
    # Calculate totals
    total_in = StockTransaction.objects.filter(transaction_type='in').aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_out = StockTransaction.objects.filter(transaction_type='out').aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_transactions = transactions.count()
    
    context = {
        'transactions': transactions,
        'total_in': total_in,
        'total_out': total_out,
        'total_transactions': total_transactions,
        'start_date': start_date,
        'end_date': end_date,
        'type': trans_type,
    }
    
    return render(request, 'apps/stock/transactions.html', context)

@login_required
def create_sale(request):
    if request.method == 'POST':
        items = request.POST.getlist('items[]')
        quantities = request.POST.getlist('quantities[]')
        
        if not items or not quantities:
            messages.error(request, 'Please add at least one item to the sale.')
            return redirect('create_sale')
        
        sale_items = []
        total_amount = 0
        
        for item_id, quantity in zip(items, quantities):
            try:
                product = Product.objects.get(pk=item_id)
                quantity = int(quantity)
                if quantity <= 0:
                    continue
                
                if product.quantity < quantity:
                    messages.error(request, f'Insufficient stock for {product.name}')
                    return redirect('create_sale')
                
                item_total = quantity * product.price
                total_amount += item_total
                
                sale_items.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'quantity': quantity,
                    'price': float(product.price),
                    'total': float(item_total)
                })
                
            except (Product.DoesNotExist, ValueError):
                continue
        
        if not sale_items:
            messages.error(request, 'No valid items in the sale.')
            return redirect('create_sale')
        
        # Generate invoice number
        invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{Sale.objects.count() + 1:04d}"
        
        sale = Sale.objects.create(
            invoice_number=invoice_number,
            customer_name=request.POST.get('customer_name', ''),
            customer_phone=request.POST.get('customer_phone', ''),
            items=sale_items,
            total_amount=total_amount,
            payment_method=request.POST.get('payment_method', 'cash'),
            payment_status=True if request.POST.get('payment_status') == 'true' else False,
            created_by=request.user
        )
        
        # Update stock quantities
        for item in sale_items:
            product = Product.objects.get(pk=item['product_id'])
            product.quantity -= item['quantity']
            product.save()
            
            # Record stock transaction
            StockTransaction.objects.create(
                product=product,
                transaction_type='out',
                quantity=item['quantity'],
                reference=f"Sale: {invoice_number}",
                notes=f"Sold to {sale.customer_name}",
                created_by=request.user
            )
        
        messages.success(request, f'Sale #{invoice_number} created successfully!')
        return redirect('sale_detail', pk=sale.id)
    
    products = Product.objects.filter(quantity__gt=0).order_by('name')
    return render(request, 'apps/sales/create.html', {'products': products})

@login_required
def sale_list(request):
    sales = Sale.objects.select_related('created_by').order_by('-created_at')
    
    # Filter by date if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search')
    
    if start_date and end_date:
        sales = sales.filter(created_at__date__range=[start_date, end_date])
    
    if search_query:
        sales = sales.filter(
            Q(invoice_number__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(customer_phone__icontains=search_query)
        )
    
    context = {
        'sales': sales,
        'start_date': start_date,
        'end_date': end_date,
        'search': search_query,
    }
    
    return render(request, 'apps/sales/list.html', context)

@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    
    # Calculate item totals for display
    items_with_total = []
    for item in sale.items:
        items_with_total.append({
            **item,
            'total': float(item['price']) * item['quantity']
        })
    
    context = {
        'sale': sale,
        'items': items_with_total,
    }
    
    return render(request, 'apps/sales/detail.html', context)

@login_required
def reports(request):
    sales = Sale.objects.all()
    
    # Default date range: last 30 days
    end_date_str = request.GET.get('end_date')
    start_date_str = request.GET.get('start_date')
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            end_date = timezone.now().date()
    else:
        end_date = timezone.now().date()
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=30)
    
    # Apply date filter
    sales = sales.filter(created_at__date__range=[start_date, end_date])
    
    # Calculate statistics
    total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_transactions = sales.count()
    average_sale = sales.aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    # Calculate growth rate
    previous_start = start_date - timedelta(days=30)
    previous_end = end_date - timedelta(days=30)
    previous_sales = Sale.objects.filter(
        created_at__date__range=[previous_start, previous_end]
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    growth_rate = 0
    if previous_sales > 0:
        growth_rate = ((total_sales - previous_sales) / previous_sales) * 100
    
    # Top selling products
    top_products = []
    for sale in sales:
        for item in sale.items:
            product_name = item['product_name']
            quantity = item['quantity']
            
            found = False
            for top_product in top_products:
                if top_product['name'] == product_name:
                    top_product['quantity'] += quantity
                    top_product['revenue'] += item['total']
                    found = True
                    break
            
            if not found:
                top_products.append({
                    'name': product_name,
                    'quantity': quantity,
                    'revenue': item['total'],
                    'avg_price': item['price']
                })
    
    # Sort by quantity and limit to top 10
    top_products = sorted(top_products, key=lambda x: x['quantity'], reverse=True)[:10]
    
    # Prepare chart data
    chart_dates = []
    chart_sales = []
    current_date = start_date
    while current_date <= end_date:
        daily_sales = Sale.objects.filter(created_at__date=current_date).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        chart_dates.append(current_date.strftime('%b %d'))
        chart_sales.append(float(daily_sales))
        current_date += timedelta(days=1)
    
    # Payment method distribution
    payment_methods = ['cash', 'card', 'transfer', 'credit']
    payment_counts = {}
    for method in payment_methods:
        payment_counts[method] = sales.filter(payment_method=method).count()
    
    context = {
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'average_sale': average_sale,
        'growth_rate': round(growth_rate, 2),
        'sales': sales[:50],
        'top_products': top_products,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'chart_dates': chart_dates,
        'chart_sales': chart_sales,
        'payment_counts': payment_counts,
    }
    
    return render(request, 'apps/reports/index.html', context)

@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # User activity statistics
    user_sales_count = Sale.objects.filter(created_by=request.user).count()
    user_products_count = Product.objects.filter(created_by=request.user).count()
    user_transactions_count = StockTransaction.objects.filter(created_by=request.user).count()
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    context = {
        'form': form,
        'user_sales_count': user_sales_count,
        'user_products_count': user_products_count,
        'user_transactions_count': user_transactions_count,
    }
    
    return render(request, 'apps/profile.html', context)

def get_product_info(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'stock': product.quantity,
            'unit': product.unit,
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)