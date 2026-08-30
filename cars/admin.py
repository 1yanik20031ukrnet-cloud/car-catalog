from django import forms
from django.contrib import admin
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.widgets import UnfoldAdminTextInputWidget

from .models import Booking, Car, CarImage, COMMON_CAR_BRANDS, Dealer


class MultipleFileInput(forms.ClearableFileInput):
    """File input that lets the user pick several files at once.

    Also renders an empty container right after itself; admin_photos.js
    fills it with instant thumbnail previews of the picked files (pure
    client-side, nothing is uploaded until the form is actually saved).
    """

    allow_multiple_selected = True

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        preview = format_html(
            '<div id="{}-preview" class="photos-preview"></div>', f'id_{name}',
        )
        return mark_safe(f'{html}{preview}')


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


class BrandInput(UnfoldAdminTextInputWidget):
    """Text input with a <datalist> of brand suggestions.

    Still a plain text field — a brand not in the list can be typed
    too — the datalist just makes the browser suggest matches as the
    person types, so existing brands stay spelled consistently.
    """

    def __init__(self, options=(), attrs=None):
        super().__init__(attrs)
        self.options = options

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs']['list'] = f'{name}-datalist'
        return context

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        options_html = format_html_join(
            '', '<option value="{}">', ((option,) for option in self.options),
        )
        datalist_html = format_html(
            '<datalist id="{}">{}</datalist>', f'{name}-datalist', options_html,
        )
        return mark_safe(f'{html}{datalist_html}')


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

    class Media:
        js = ['cars/admin_photos.js']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing_brands = (
            Car.objects.exclude(brand='').values_list('brand', flat=True).distinct()
        )
        brand_options = sorted(
            set(COMMON_CAR_BRANDS) | set(existing_brands), key=str.casefold,
        )
        self.fields['brand'].widget = BrandInput(
            options=brand_options, attrs=self.fields['brand'].widget.attrs,
        )


@admin.register(Dealer)
class DealerAdmin(ModelAdmin):
    list_display = ['name', 'phone', 'currency']


class CarImageInlineForm(forms.ModelForm):
    """Hides the raw image widget — replacing files happens by deleting
    a photo here and adding a new one through the top upload field, not
    by editing this row's file path in place."""

    class Meta:
        model = CarImage
        fields = ['image', 'order']
        widgets = {'image': forms.HiddenInput()}


class CarImageInline(TabularInline):
    """Photos already uploaded: drag to reorder, or delete.

    Adding new photos happens through the 'Загрузить фотографии' field
    above, so this inline never offers its own 'add another' row.
    Dragging a row is handled entirely by django-unfold's built-in
    sortable inlines (ordering_field) — no custom JS needed for that.
    """

    model = CarImage
    form = CarImageInlineForm
    extra = 0
    verbose_name_plural = 'Уже загруженные фотографии — перетащите, чтобы поменять порядок'
    fields = ['preview', 'image', 'order']
    readonly_fields = ['preview']
    ordering_field = 'order'
    hide_ordering_field = True

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='')
    def preview(self, obj):
        if not obj.image:
            return '—'
        return format_html(
            '<div class="photo-preview-cell">'
            '<img src="{}" style="height:70px;border-radius:4px;">'
            '<span class="cover-badge">Обложка</span>'
            '</div>',
            obj.image.url,
        )


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
