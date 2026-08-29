from django.contrib import admin
from django.utils.html import format_html

from .models import Booking, Car, CarImage, Dealer


@admin.register(Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'currency']


class CarImageInline(admin.TabularInline):
    """Фотографии редактируются прямо на странице автомобиля."""

    model = CarImage
    extra = 1
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
class CarAdmin(admin.ModelAdmin):
    list_display = ['photo', '__str__', 'price_display', 'mileage_km', 'status', 'created_at']
    list_filter = ['status', 'brand', 'fuel', 'transmission']
    search_fields = ['brand', 'model', 'vin']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    inlines = [CarImageInline]
    actions = ['mark_sold']

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

    @admin.action(description='Отметить выбранные автомобили проданными')
    def mark_sold(self, request, queryset):
        updated = queryset.update(status=Car.Status.SOLD)
        self.message_user(request, f'Продано автомобилей: {updated}')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'car', 'date', 'preferred_time', 'created_at']
    list_filter = ['date']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at']
