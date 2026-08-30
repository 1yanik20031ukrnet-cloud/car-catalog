from django import forms
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from .models import Booking, Car, CarImage, Dealer


class MultipleFileInput(forms.ClearableFileInput):
    """File input that lets the user pick several files at once."""

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """FileField that validates and returns a list of uploaded files."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if not isinstance(data, (list, tuple)):
            data = [data] if data else []
        return [single_clean(item, initial) for item in data if item]


class CarAdminForm(forms.ModelForm):
    """Car form with a single 'pick many photos at once' field."""

    photos = MultipleFileField(
        label='Загрузить фотографии',
        required=False,
        help_text='Можно выделить сразу несколько файлов. '
                  'Первое фото станет главным в каталоге. '
                  'Совет: если форма ниже покажет ошибку и её придётся '
                  'исправлять — выберите фотографии заново, браузер '
                  'сбрасывает выбор файлов при повторной отправке.',
    )

    class Meta:
        model = Car
        fields = '__all__'


@admin.register(Dealer)
class DealerAdmin(ModelAdmin):
    list_display = ['name', 'phone', 'currency']


class CarImageInline(TabularInline):
    """Photos already uploaded: reorder, replace or delete them."""

    model = CarImage
    extra = 0
    verbose_name_plural = 'Уже загруженные фотографии'
    fields = ['preview', 'image', 'order']
    readonly_fields = ['preview']

    @admin.display(description='Превью')
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px;border-radius:4px;">',
                obj.image.url,
            )
        return '—'


@admin.register(Car)
class CarAdmin(ModelAdmin):
    form = CarAdminForm
    list_display = ['photo', '__str__', 'price_display', 'mileage_km', 'status_badge', 'created_at']
    list_filter = ['status', 'brand', 'fuel', 'transmission']
    search_fields = ['brand', 'model', 'vin']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    inlines = [CarImageInline]
    actions = ['mark_sold']

    fieldsets = [
        ('Фотографии', {
            'fields': ['photos'],
        }),
        ('Основное', {
            'fields': ['dealer', 'brand', 'model', 'year', 'price', 'status'],
        }),
        ('Характеристики', {
            'fields': [
                'mileage_km', 'fuel', 'transmission',
                'engine_capacity', 'power_hp', 'drive', 'body',
            ],
        }),
        ('Описание и VIN', {
            'fields': ['description', 'vin'],
        }),
        ('Внутренняя заметка (не видна на сайте)', {
            'fields': ['internal_note'],
        }),
        ('Служебное (заполняется автоматически)', {
            'fields': ['slug', 'created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]

    @admin.display(description='Фото')
    def photo(self, obj):
        image = obj.main_image
        if image:
            return format_html(
                '<img src="{}" style="height:45px;border-radius:4px;">',
                image.image.url,
            )
        return '—'

    @admin.display(description='Цена', ordering='price')
    def price_display(self, obj):
        return f'{obj.price:,} {obj.dealer.currency}'.replace(',', ' ')

    @display(description='Статус', label={
        Car.Status.FOR_SALE: 'success',
        Car.Status.RESERVED: 'warning',
        Car.Status.SOLD: 'danger',
    })
    def status_badge(self, obj):
        return obj.status, obj.get_status_display()

    def save_related(self, request, form, formsets, change):
        """Save inline photo edits, then append the newly uploaded photos."""
        super().save_related(request, form, formsets, change)
        photos = form.cleaned_data.get('photos') or []
        if not photos:
            return
        car = form.instance
        last = car.images.order_by('-order').first()
        next_order = last.order + 1 if last else 0
        for offset, photo in enumerate(photos):
            CarImage.objects.create(
                car=car, image=photo, order=next_order + offset,
            )

    @admin.action(description='Отметить выбранные автомобили проданными')
    def mark_sold(self, request, queryset):
        updated = queryset.update(status=Car.Status.SOLD)
        self.message_user(request, f'Продано автомобилей: {updated}')


@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    list_display = ['name', 'phone', 'car', 'date', 'preferred_time', 'created_at']
    list_filter = ['date']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at']
