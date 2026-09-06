from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.widgets import UnfoldAdminTextInputWidget

from . import formatting
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
        # is_published deliberately excluded: it's not shown as a
        # field in any fieldset any more (just a status badge next to
        # the buttons, see templates/admin/submit_line.html), and if
        # it stayed in the form, a plain "Сохранить" would silently
        # reset it to False — Django treats a checkbox missing from
        # the page the same as an unchecked one. Only the "Опубликовать"
        # button (CarAdmin.save_model) and the two list actions
        # (publish_cars / unpublish_cars) are meant to change it.
        exclude = ['is_published']

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
    readonly_fields = ['logo_preview']
    fields = [
        'name', 'logo_preview', 'logo', 'description', 'phone',
        'instagram', 'telegram', 'whatsapp',
        'currency', 'secondary_currency', 'exchange_rate',
    ]

    @admin.display(description='Текущий логотип')
    def logo_preview(self, obj):
        if not obj.logo:
            return 'Логотип ещё не загружен — в шапке сайта показывается название.'
        return format_html(
            '<img src="{}" style="max-width:180px;max-height:90px;'
            'border-radius:6px;display:block;background:#fff;padding:8px;">',
            obj.logo.url,
        )


class CarImageInlineForm(forms.ModelForm):
    """Leaves 'image' out of the form entirely — replacing a file
    happens by deleting a photo here and adding a new one through the
    top upload field, not by editing this row's file in place.

    Earlier this hid the field with forms.HiddenInput() instead of
    leaving it out — that rendered a hidden input whose value was the
    file's *path as plain text*. Django resubmits that text on every
    save, and FileField can't accept a plain string as a file, so it
    silently failed validation with no visible error (the field had
    no visible spot to show one) — every re-save of a car that already
    had photos was broken. Leaving 'image' out of the form's own
    fields entirely means nothing gets posted for it at all, so
    Django correctly keeps the existing file untouched. (2026-09-01)
    """

    class Meta:
        model = CarImage
        fields = ['order']


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
    fields = ['preview', 'order']
    readonly_fields = ['preview']
    ordering_field = 'order'
    hide_ordering_field = True

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='')
    def preview(self, obj):
        if not obj.image:
            return '—'
        # x-sort:handle (unfold/alpine.sort.js) makes this whole card a
        # drag handle, not just the small drag_indicator icon it ships
        # with — grabbing the photo itself, or the space around it,
        # now starts a drag too.
        return format_html(
            '<div class="photo-preview-cell" x-sort:handle>'
            '<img class="photo-thumb" src="{}">'
            '<span class="cover-badge">Обложка</span>'
            '</div>',
            obj.image.url,
        )


@admin.register(Car)
class CarAdmin(ModelAdmin):
    form = CarAdminForm
    list_display = [
        'photo', '__str__', 'price_display', 'mileage_km',
        'status_badge', 'is_published', 'created_at',
    ]
    list_filter = ['status', 'is_published', 'brand', 'fuel', 'transmission', 'accident', 'negotiable']
    search_fields = ['brand', 'model', 'vin']
    readonly_fields = ['slug', 'created_at', 'updated_at', 'video_preview']
    inlines = [CarImageInline]
    actions = ['mark_sold', 'publish_cars', 'unpublish_cars']

    fieldsets = [
        ('Фотографии', {
            'fields': ['photos'],
        }),
        ('Видео', {
            'fields': ['video_preview', 'video'],
        }),
        ('Основное', {
            'fields': ['dealer', 'brand', 'model', 'year', 'price', 'status', 'sold_at'],
        }),
        ('Характеристики', {
            'fields': [
                'mileage_km', 'fuel', 'transmission',
                'engine_capacity', 'power_hp', 'drive', 'body',
            ],
        }),
        ('Отметки на сайте', {
            'description': 'Показываются на странице автомобиля тремя '
                           'плашками рядом с ценой.',
            'fields': ['accident', 'imported_from', 'negotiable'],
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

    @admin.display(description='Текущее видео')
    def video_preview(self, obj):
        if not obj.video:
            return 'Видео ещё не загружено.'
        return format_html(
            '<video controls style="max-width:280px;max-height:160px;'
            'border-radius:6px;display:block;">'
            '<source src="{}">'
            'Браузер не может показать видео.'
            '</video>',
            obj.video.url,
        )

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
        return formatting.format_price(obj.price, obj.dealer.currency)

    @display(description='Статус', label={
        Car.Status.FOR_SALE: 'success',
        Car.Status.RESERVED: 'warning',
        Car.Status.SOLD: 'danger',
    })
    def status_badge(self, obj):
        return obj.status, obj.get_status_display()

    def save_model(self, request, obj, form, change):
        """The 'Опубликовать' button (templates/admin/submit_line.html)
        submits the normal form plus a `_publish` flag — flip the field
        here so it's published even if the checkbox further down the
        form wasn't touched."""
        if '_publish' in request.POST:
            obj.is_published = True
        super().save_model(request, obj, form, change)

    def response_change(self, request, obj):
        """After '_publish', stay on the same page (like 'Сохранить →
        остаться здесь') instead of Django's default redirect, so the
        owner immediately sees the checkbox is now checked."""
        if '_publish' in request.POST:
            self.message_user(request, f'«{obj}» опубликован(а) на сайте.')
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        """Same '_publish' handling for a brand-new car — land on its
        own edit page afterwards rather than Django's default (the
        changelist), since that's the more useful place to be right
        after creating and publishing one."""
        if '_publish' in request.POST:
            self.message_user(request, f'«{obj}» создан(а) и опубликован(а) на сайте.')
            return HttpResponseRedirect(
                reverse('admin:cars_car_change', args=[obj.pk]),
            )
        return super().response_add(request, obj, post_url_continue)

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
        # queryset.update() не вызывает Car.save() (там автопроставление
        # sold_at), поэтому дату здесь ставим отдельно — и только тем, у
        # кого её ещё нет. Id считаем заранее, до первого update(): иначе
        # второй фильтр увидел бы уже обновлённые этим же действием
        # машины (у них sold_at успел бы стать не пустым) и посчитал бы
        # их второй раз.
        without_date = list(
            queryset.filter(sold_at__isnull=True).values_list('pk', flat=True),
        )
        with_date = list(
            queryset.filter(sold_at__isnull=False).values_list('pk', flat=True),
        )
        if without_date:
            Car.objects.filter(pk__in=without_date).update(
                status=Car.Status.SOLD, sold_at=timezone.now(),
            )
        if with_date:
            Car.objects.filter(pk__in=with_date).update(status=Car.Status.SOLD)
        self.message_user(request, f'Продано автомобилей: {len(without_date) + len(with_date)}')

    @admin.action(description='Опубликовать выбранные автомобили на сайте')
    def publish_cars(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'Опубликовано автомобилей: {updated}')

    @admin.action(description='Снять выбранные автомобили с публикации')
    def unpublish_cars(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'Снято с публикации: {updated}')


@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    list_display = ['name', 'phone', 'car_link', 'date', 'preferred_time', 'created_at']
    list_filter = ['date']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at']

    @admin.display(description='Автомобиль', ordering='car')
    def car_link(self, obj):
        """Прямая ссылка на карточку машины в админке — чтобы не искать
        вручную, какую именно машину показывать по этой заявке."""
        url = reverse('admin:cars_car_change', args=[obj.car_id])
        return format_html('<a href="{}">{}</a>', url, obj.car)
