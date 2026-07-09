from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Товары
    path('', views.product_list, name='product_list'),
    path('add/', views.product_add, name='product_add'),
    path('edit/<int:product_id>/', views.product_edit, name='product_edit'),
    path('delete/<int:product_id>/', views.product_delete, name='product_delete'),
    
    # Корзина
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('cart/count/', views.cart_count, name='cart_count'),
    
    # Заказы
    path('order/create/', views.order_create, name='order_create'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('all-orders/', views.all_orders, name='all_orders'),
    path('order/manage/<int:order_id>/', views.order_manage, name='order_manage'),
    
    # Профиль
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]