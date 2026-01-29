from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # User Management
    path('users/create/', views.create_user, name='create_user'),
    path('users/', views.user_list, name='user_list'),
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('products/delete/<int:pk>/', views.product_delete, name='product_delete'),
    
    # Stock Management
    path('stock/in/', views.stock_in, name='stock_in'),
    path('stock/out/', views.stock_out, name='stock_out'),
    path('stock/transactions/', views.stock_transactions, name='stock_transactions'),
    
    # Sales
    path('sales/create/', views.create_sale, name='create_sale'),
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    
    # AJAX endpoints
    path('api/product/<int:product_id>/', views.get_product_info, name='get_product_info'),
]