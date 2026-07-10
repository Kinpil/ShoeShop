from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Расширенная модель пользователя
    Добавляет роль и ФИО для всех пользователей системы
    """
    ROLE_CHOICES = (
        ('guest', 'Гость'),
        ('client', 'Клиент'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='guest',
        verbose_name='Роль'
    )
    full_name = models.CharField(
        max_length=150, 
        verbose_name='ФИО',
        blank=True
    )
    birth_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name='Дата рождения'
    )

    def __str__(self):
        return self.full_name or self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Category(models.Model):
    """
    Справочник категорий товаров
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Manufacturer(models.Model):
    """
    Справочник производителей
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'


class Supplier(models.Model):
    """
    Справочник поставщиков
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'


class Product(models.Model):
    """
    Модель товара
    Содержит все поля из технического задания
    """
    name = models.CharField(max_length=200, verbose_name='Наименование товара')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, verbose_name='Производитель')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name='Поставщик')
    description = models.TextField(blank=True, verbose_name='Описание товара')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    unit = models.CharField(max_length=20, verbose_name='Единица измерения')
    stock = models.IntegerField(default=0, verbose_name='Количество на складе')
    discount = models.IntegerField(default=0, verbose_name='Действующая скидка')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Фото товара')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return self.name

    def get_price_with_discount(self):
        if self.discount > 0:
            return self.price * (100 - self.discount) / 100
        return self.price

    def has_orders(self):
        return self.orderitem_set.exists()

    def get_average_rating(self):
        """Возвращает средний рейтинг товара"""
        reviews = self.reviews.all()
        if reviews:
            return sum(r.rating for r in reviews) / len(reviews)
        return 0

    def get_reviews_count(self):
        """Возвращает количество отзывов"""
        return self.reviews.count()

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name']


class Cart(models.Model):
    """
    Корзина пользователя
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return f'Корзина {self.user.username}'

    def get_total(self):
        total = 0
        for item in self.items.all():
            total += item.product.get_price_with_discount() * item.quantity
        return total

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'


class CartItem(models.Model):
    """
    Товар в корзине
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name='Корзина')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.IntegerField(default=1, verbose_name='Количество')
    price_at_add = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена при добавлении')

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def get_total(self):
        return self.price_at_add * self.quantity

    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'


class Order(models.Model):
    """
    Модель заказа
    """
    STATUS_CHOICES = (
        ('pending', 'В обработке'),
        ('processing', 'Собирается'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    products = models.ManyToManyField(Product, through='OrderItem', verbose_name='Товары')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Общая стоимость')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    address = models.TextField(blank=True, verbose_name='Адрес доставки')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')

    def __str__(self):
        return f'Заказ #{self.id} - {self.user.full_name or self.user.username} - {self.get_status_display()}'

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']


class OrderItem(models.Model):
    """
    Промежуточная модель для заказа и товара
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, verbose_name='Количество')
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена при заказе')

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'


class Review(models.Model):
    """
    Отзыв на товар
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name='Товар')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    rating = models.IntegerField(
        choices=[(i, f'{i} ★') for i in range(1, 6)],
        verbose_name='Оценка'
    )
    text = models.TextField(verbose_name='Текст отзыва')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f'{self.user.username} - {self.product.name} - {self.rating}★'

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        unique_together = ['product', 'user']


class Wishlist(models.Model):
    """
    Избранное пользователя
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist', verbose_name='Пользователь')
    products = models.ManyToManyField(Product, related_name='wishlisted_by', verbose_name='Товары в избранном')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return f'Избранное {self.user.username}'

    def get_count(self):
        return self.products.count()

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'