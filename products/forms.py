from django import forms
from .models import Product, Category, Manufacturer, Supplier, Review


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'manufacturer', 'supplier', 'description', 
                  'price', 'unit', 'stock', 'discount', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'min': '0', 'max': '100', 'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('шт.', 'шт. (штуки)'),
                ('пар', 'пар (пары)'),
                ('кг', 'кг (килограммы)'),
                ('м', 'м (метры)'),
                ('см', 'см (сантиметры)'),
                ('л', 'л (литры)'),
            ]),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Наименование товара',
            'category': 'Категория',
            'manufacturer': 'Производитель',
            'supplier': 'Поставщик',
            'description': 'Описание товара',
            'price': 'Цена',
            'unit': 'Единица измерения',
            'stock': 'Количество на складе',
            'discount': 'Действующая скидка (%)',
            'image': 'Фото товара',
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Напишите ваш отзыв...'}),
        }
        labels = {
            'rating': 'Оценка',
            'text': 'Текст отзыва',
        }