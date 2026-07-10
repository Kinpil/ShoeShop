from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import JsonResponse, FileResponse
from PIL import Image
from .models import Product, Category, Manufacturer, Supplier, OrderItem, Cart, CartItem, Order, Review, Wishlist
from .forms import ProductForm, ReviewForm
import os
import io
from django.conf import settings
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def product_list(request):
    """Отображение списка товаров с поиском, фильтрацией и сортировкой"""
    products = Product.objects.all()
    suppliers = Supplier.objects.all()
    categories = Category.objects.all()
    
    # Определяем роль пользователя
    user_role = request.user.role if request.user.is_authenticated else 'guest'
    
    # Поиск, фильтрация и сортировка ДОСТУПНЫ только для менеджера и администратора
    if user_role in ['manager', 'admin']:
        # Поиск
        search_query = request.GET.get('search', '')
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(manufacturer__name__icontains=search_query) |
                Q(supplier__name__icontains=search_query)
            )
        
        # Фильтрация по поставщику
        supplier_filter = request.GET.get('supplier', '')
        if supplier_filter:
            products = products.filter(supplier__id=supplier_filter)
        
        # Фильтрация по категории
        category_filter = request.GET.get('category', '')
        if category_filter:
            products = products.filter(category__id=category_filter)
        
        # Фильтр по цене (диапазон)
        price_min = request.GET.get('price_min', '')
        price_max = request.GET.get('price_max', '')
        if price_min:
            products = products.filter(price__gte=price_min)
        if price_max:
            products = products.filter(price__lte=price_max)
        
        # Сортировка по количеству
        sort_by = request.GET.get('sort', '')
        if sort_by == 'stock_asc':
            products = products.order_by('stock')
        elif sort_by == 'stock_desc':
            products = products.order_by('-stock')
        else:
            products = products.order_by('name')
    else:
        # Для гостя и клиента — без поиска, фильтрации и сортировки
        search_query = ''
        supplier_filter = ''
        category_filter = ''
        price_min = ''
        price_max = ''
        sort_by = ''
        products = products.order_by('name')
    
    # Пагинация — 12 товаров на страницу
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'suppliers': suppliers,
        'categories': categories,
        'search_query': search_query,
        'supplier_filter': supplier_filter,
        'category_filter': category_filter,
        'price_min': price_min,
        'price_max': price_max,
        'sort_by': sort_by,
        'user_role': user_role,
    }
    return render(request, 'products/list.html', context)


@staff_member_required
def product_add(request):
    """Добавление нового товара (только для администратора)"""
    if request.user.role != 'admin':
        messages.error(request, 'У вас нет прав для добавления товаров!')
        return redirect('products:product_list')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            if 'image' in request.FILES:
                product.image = resize_image(request.FILES['image'])
            product.save()
            messages.success(request, f'Товар "{product.name}" успешно добавлен!')
            return redirect('products:product_list')
    else:
        form = ProductForm()
    
    return render(request, 'products/product_form.html', {
        'form': form, 
        'title': 'Добавление товара'
    })


@staff_member_required
def product_edit(request, product_id):
    """Редактирование товара (только для администратора)"""
    if request.user.role != 'admin':
        messages.error(request, 'У вас нет прав для редактирования товаров!')
        return redirect('products:product_list')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        # ОТЛАДКА: выводим в терминал, что пришло в запросе
        print('🔍 POST данные:', request.POST)
        print('📁 FILES данные:', request.FILES)
        
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            if 'image' in request.FILES:
                # Удаляем старое фото, если оно есть
                if product.image:
                    old_image_path = os.path.join(settings.MEDIA_ROOT, str(product.image))
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                product.image = resize_image(request.FILES['image'])
            product.save()
            messages.success(request, f'Товар "{product.name}" успешно обновлен!')
            return redirect('products:product_list')
        else:
            print('❌ Форма не валидна:', form.errors)
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Редактирование товара',
        'product': product,
        'product_id': product_id,
    })


@staff_member_required
def product_delete(request, product_id):
    """Удаление товара (только для администратора)"""
    if request.user.role != 'admin':
        messages.error(request, 'У вас нет прав для удаления товаров!')
        return redirect('products:product_list')
    
    product = get_object_or_404(Product, id=product_id)
    order_items = OrderItem.objects.filter(product=product)
    
    if request.method == 'POST':
        if order_items.exists():
            messages.error(request, f'Невозможно удалить товар "{product.name}". Он присутствует в заказах!')
            return redirect('products:product_list')
        
        product_name = product.name
        if product.image:
            image_path = os.path.join(settings.MEDIA_ROOT, str(product.image))
            if os.path.exists(image_path):
                os.remove(image_path)
        product.delete()
        messages.success(request, f'Товар "{product_name}" успешно удален!')
        return redirect('products:product_list')
    
    return render(request, 'products/product_confirm_delete.html', {
        'product': product,
        'has_orders': order_items.exists(),
    })


# === КОРЗИНА ===

@login_required
def cart_view(request):
    """Отображение корзины"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    total = cart.get_total()
    return render(request, 'products/cart.html', {'items': items, 'total': total})


@login_required
def cart_add(request, product_id):
    """Добавление товара в корзину"""
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'price_at_add': product.price}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f'Количество товара "{product.name}" увеличено!')
    else:
        messages.success(request, f'Товар "{product.name}" добавлен в корзину!')
    
    return redirect('products:cart')


@login_required
def cart_remove(request, item_id):
    """Удаление товара из корзины"""
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    product_name = item.product.name
    item.delete()
    messages.success(request, f'Товар "{product_name}" удален из корзины!')
    return redirect('products:cart')


@login_required
def cart_update(request, item_id):
    """Обновление количества товара в корзине"""
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            item.quantity = quantity
            item.save()
            messages.success(request, f'Количество товара "{item.product.name}" обновлено!')
        else:
            item.delete()
            messages.success(request, f'Товар "{item.product.name}" удален из корзины!')
    
    return redirect('products:cart')


@login_required
def cart_count(request):
    """Возвращает количество товаров в корзине пользователя"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    count = sum(item.quantity for item in cart.items.all())
    return JsonResponse({'count': count})


# === ЗАКАЗЫ ===

@login_required
def order_create(request):
    """Оформление заказа из корзины"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    
    if not items:
        messages.warning(request, 'Корзина пуста!')
        return redirect('products:cart')
    
    # Проверяем наличие товаров на складе
    out_of_stock_items = []
    for item in items:
        if item.quantity > item.product.stock:
            out_of_stock_items.append(f'{item.product.name} (доступно: {item.product.stock})')
    
    if out_of_stock_items:
        messages.error(request, f'Невозможно оформить заказ. Товаров нет в наличии: {", ".join(out_of_stock_items)}')
        return redirect('products:cart')
    
    if request.method == 'POST':
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Валидация телефона — только цифры, не более 12
        phone_clean = ''.join(filter(str.isdigit, phone))
        if not phone_clean or len(phone_clean) > 12:
            messages.error(request, 'Введите корректный номер телефона (только цифры, не более 12 символов)')
            return render(request, 'products/order_create.html', {
                'items': items,
                'total': cart.get_total()
            })
        
        if not address:
            messages.error(request, 'Введите адрес доставки!')
            return render(request, 'products/order_create.html', {
                'items': items,
                'total': cart.get_total()
            })
        
        # Создаём заказ
        total_with_discount = 0
        order = Order.objects.create(
            user=request.user,
            total_price=0,
            address=address,
            phone=phone_clean,
            status='pending'
        )
        
        # Переносим товары из корзины в заказ с учётом скидки
        for item in items:
            discounted_price = item.product.get_price_with_discount()
            
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_order=discounted_price
            )
            
            total_with_discount += discounted_price * item.quantity
            
            # Уменьшаем количество на складе
            product = item.product
            product.stock -= item.quantity
            product.save()
        
        order.total_price = total_with_discount
        order.save()
        
        # Очищаем корзину
        items.delete()
        
        messages.success(request, f'Заказ #{order.id} успешно оформлен!')
        return redirect('products:order_detail', order_id=order.id)
    
    return render(request, 'products/order_create.html', {
        'items': items,
        'total': cart.get_total()
    })


@login_required
def order_detail(request, order_id):
    """Просмотр деталей заказа"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.user.role == 'client' and order.user != request.user:
        messages.error(request, 'У вас нет доступа к этому заказу!')
        return redirect('products:my_orders')
    
    items = order.orderitem_set.all()
    return render(request, 'products/order_detail.html', {
        'order': order,
        'items': items
    })


@login_required
def my_orders(request):
    """Список заказов текущего пользователя (для клиента)"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'products/my_orders.html', {'orders': orders})


@login_required
def all_orders(request):
    """Список всех заказов (для менеджера и администратора)"""
    if request.user.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет доступа к этой странице!')
        return redirect('products:product_list')
    
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'products/all_orders.html', {'orders': orders})


@login_required
def order_manage(request, order_id):
    """Управление заказом (только для администратора)"""
    if request.user.role != 'admin':
        messages.error(request, 'У вас нет прав для управления заказами!')
        return redirect('products:product_list')
    
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                order.save()
                messages.success(request, f'Статус заказа #{order.id} обновлён на "{order.get_status_display()}"')
        elif action == 'delete':
            order.delete()
            messages.success(request, f'Заказ #{order.id} удалён!')
            return redirect('products:all_orders')
    
    return redirect('products:order_detail', order_id=order.id)


# === PDF ===

@login_required
def order_pdf(request, order_id):
    """Генерация PDF-файла заказа"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.user.role == 'client' and order.user != request.user:
        messages.error(request, 'У вас нет доступа к этому заказу!')
        return redirect('products:my_orders')
    
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf')
    
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        use_font = 'DejaVuSans'
    else:
        use_font = 'Helvetica'
    
    buffer = io.BytesIO()
    
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    c.setFont(use_font, 18)
    c.drawString(50, height - 50, 'ShoeShop')
    c.setFont(use_font, 10)
    c.drawString(50, height - 70, 'Интернет-магазин обуви')
    
    c.line(50, height - 80, width - 50, height - 80)
    
    y = height - 110
    c.setFont(use_font, 14)
    c.drawString(50, y, f'Заказ № {order.id}')
    y -= 20
    c.setFont(use_font, 11)
    c.drawString(50, y, f'Дата: {order.created_at.strftime("%d.%m.%Y %H:%M")}')
    y -= 16
    c.drawString(50, y, f'Статус: {order.get_status_display()}')
    y -= 16
    c.drawString(50, y, f'Покупатель: {order.user.full_name or order.user.username}')
    y -= 16
    c.drawString(50, y, f'Адрес доставки: {order.address}')
    y -= 16
    c.drawString(50, y, f'Телефон: {order.phone}')
    y -= 25
    
    items = order.orderitem_set.all()
    
    c.setFont(use_font, 11)
    c.drawString(50, y, '№')
    c.drawString(80, y, 'Товар')
    c.drawString(320, y, 'Кол-во')
    c.drawString(380, y, 'Цена')
    c.drawString(450, y, 'Сумма')
    y -= 10
    
    c.line(50, y + 5, width - 50, y + 5)
    y -= 12
    
    c.setFont(use_font, 10)
    total = 0
    i = 1
    for item in items:
        subtotal = item.quantity * item.price_at_order
        total += subtotal
        
        c.drawString(50, y, str(i))
        c.drawString(80, y, item.product.name[:30])
        c.drawString(320, y, str(item.quantity))
        c.drawString(380, y, f'{item.price_at_order:.2f} руб.')
        c.drawString(450, y, f'{subtotal:.2f} руб.')
        
        y -= 18
        i += 1
        
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont(use_font, 10)
    
    y -= 5
    c.line(50, y + 10, width - 50, y + 10)
    y -= 15
    c.setFont(use_font, 13)
    c.drawString(380, y, f'Итого: {total:.2f} руб.')
    
    c.setFont(use_font, 9)
    c.drawString(50, 50, 'Спасибо за покупку!')
    c.drawString(50, 35, '© 2026 ShoeShop. Все права защищены.')
    
    c.save()
    buffer.seek(0)
    
    return FileResponse(buffer, as_attachment=True, filename=f'Заказ_{order.id}.pdf')


# === ПРОФИЛЬ ===

@login_required
def profile(request):
    """Личный кабинет пользователя"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'products/profile.html', {
        'user': request.user,
        'orders': orders
    })


@login_required
def profile_edit(request):
    """Редактирование профиля пользователя"""
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        birth_date = request.POST.get('birth_date', '').strip()
        
        user = request.user
        if full_name:
            user.full_name = full_name
        if email:
            user.email = email
        if birth_date:
            try:
                user.birth_date = datetime.strptime(birth_date, '%d.%m.%Y').date()
            except ValueError:
                messages.error(request, 'Неверный формат даты рождения! Используйте ДД.ММ.ГГГГ')
                return redirect('products:profile_edit')
        
        user.save()
        messages.success(request, 'Профиль успешно обновлён!')
        return redirect('products:profile')
    
    return render(request, 'products/profile_edit.html', {
        'user': request.user
    })


# === ОТЗЫВЫ ===

@login_required
def product_detail(request, product_id):
    """Страница товара с отзывами"""
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()
    average_rating = product.get_average_rating()
    reviews_count = product.get_reviews_count()
    
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(product=product, user=request.user).first()
    
    if request.method == 'POST':
        if user_review:
            messages.warning(request, 'Вы уже оставили отзыв на этот товар!')
            return redirect('products:product_detail', product_id=product.id)
        
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Спасибо за ваш отзыв!')
            return redirect('products:product_detail', product_id=product.id)
    else:
        form = ReviewForm()
    
    context = {
        'product': product,
        'reviews': reviews,
        'average_rating': average_rating,
        'reviews_count': reviews_count,
        'user_review': user_review,
        'form': form,
    }
    return render(request, 'products/product_detail.html', context)


# === ИЗБРАННОЕ ===

@login_required
def wishlist_view(request):
    """Отображение избранного"""
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    products = wishlist.products.all()
    return render(request, 'products/wishlist.html', {'products': products})


@login_required
def wishlist_add(request, product_id):
    """Добавление товара в избранное"""
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if product in wishlist.products.all():
        messages.info(request, f'Товар "{product.name}" уже в избранном!')
    else:
        wishlist.products.add(product)
        messages.success(request, f'Товар "{product.name}" добавлен в избранное!')
    
    return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


@login_required
def wishlist_remove(request, product_id):
    """Удаление товара из избранного"""
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    wishlist.products.remove(product)
    messages.success(request, f'Товар "{product.name}" удалён из избранного!')
    return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


def resize_image(image):
    """
    Изменяет размер изображения до 300x200 с сохранением пропорций (обрезает лишнее)
    """
    try:
        img = Image.open(image)
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        target_width = 300
        target_height = 200
        
        width, height = img.size
        ratio = max(target_width / width, target_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        img = img.resize((new_width, new_height), Image.LANCZOS)
        
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        img = img.crop((left, top, right, bottom))
        
        output = BytesIO()
        img.save(output, format='PNG', quality=85)
        output.seek(0)
        
        return InMemoryUploadedFile(
            output, 
            'ImageField', 
            f"{image.name.split('.')[0]}.png", 
            'image/png', 
            output.getbuffer().nbytes, 
            None
        )
    except Exception as e:
        return image