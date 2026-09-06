from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

MAX_VIDEO_SIZE_MB = 100


def validate_video_size(file):
    """Keeps someone from filling up the server's disk with one upload."""
    limit = MAX_VIDEO_SIZE_MB * 1024 * 1024
    if file.size > limit:
        raise ValidationError(f'Видео больше {MAX_VIDEO_SIZE_MB} МБ — сожмите файл перед загрузкой.')

# Подсказки марок для админки (автодополнение) и будущего фильтра
# в каталоге. Марка у Car остаётся обычным текстовым полем — этот
# список только подсказывает, ввести можно и марку не из списка.
COMMON_CAR_BRANDS = (
    'Audi', 'BMW', 'Mercedes-Benz', 'Volkswagen', 'Porsche', 'Volvo',
    'Toyota', 'Lexus', 'Honda', 'Mazda', 'Nissan', 'Mitsubishi',
    'Subaru', 'Suzuki', 'Hyundai', 'Kia', 'Ford', 'Opel', 'Chevrolet',
    'Jeep', 'Tesla', 'Škoda', 'Renault', 'Peugeot', 'Citroën', 'Fiat',
    'Seat', 'Land Rover', 'Jaguar', 'Mini', 'Bentley',
)


class Dealer(models.Model):
    """Автосалон. Пока одна запись, но структура готова к нескольким."""

    class Currency(models.TextChoices):
        UAH = '₴', '₴ (гривна)'
        USD = '$', '$ (доллар)'
        EUR = '€', '€ (евро)'
        PLN = 'zł', 'zł (злотый)'

    name = models.CharField('Название', max_length=100)
    logo = models.ImageField(
        'Логотип', upload_to='dealer/', blank=True,
        help_text='Необязательно. Пока пусто — в шапке сайта и админке '
                  'показывается текстовое название салона, как сейчас. '
                  'Лучше всего смотрится квадратное изображение — в '
                  'админке логотип показывается в квадратной иконке.',
    )
    description = models.TextField('Короткое описание', blank=True)
    phone = models.CharField('Телефон', max_length=30)
    instagram = models.URLField('Ссылка на Instagram', blank=True)
    telegram = models.CharField('Telegram (@username)', max_length=100, blank=True)
    whatsapp = models.CharField('WhatsApp (номер)', max_length=30, blank=True)
    currency = models.CharField(
        'Валюта цен', max_length=3,
        choices=Currency.choices, default=Currency.USD,
    )
    secondary_currency = models.CharField(
        'Дополнительная валюта', max_length=3,
        choices=Currency.choices, blank=True,
        help_text='Необязательно. Если заполнено, цена на сайте '
                  'показывается сразу в двух валютах — курс для '
                  'пересчёта указывается ниже.',
    )
    exchange_rate = models.DecimalField(
        'Курс обмена', max_digits=10, decimal_places=4,
        null=True, blank=True,
        help_text='Сколько единиц дополнительной валюты за 1 единицу '
                  'основной (например, при основной $ и дополнительной '
                  '₴ — сколько гривен за доллар). Вводится вручную, '
                  'курс не подтягивается автоматически откуда-либо.',
    )

    class Meta:
        verbose_name = 'автосалон'
        verbose_name_plural = 'Автосалон'

    def __str__(self):
        return self.name


class Car(models.Model):
    """Автомобиль в каталоге."""

    class Status(models.TextChoices):
        FOR_SALE = 'for_sale', 'В продаже'
        RESERVED = 'reserved', 'Зарезервирован'
        SOLD = 'sold', 'Продан'

    class Fuel(models.TextChoices):
        PETROL = 'petrol', 'Бензин'
        DIESEL = 'diesel', 'Дизель'
        HYBRID = 'hybrid', 'Гибрид'
        ELECTRIC = 'electric', 'Электро'
        GAS = 'gas', 'Газ/Бензин'

    class Transmission(models.TextChoices):
        AUTOMATIC = 'automatic', 'Автомат'
        MANUAL = 'manual', 'Механика'

    class Drive(models.TextChoices):
        FWD = 'fwd', 'Передний'
        RWD = 'rwd', 'Задний'
        AWD = 'awd', 'Полный'

    class Body(models.TextChoices):
        SEDAN = 'sedan', 'Седан'
        WAGON = 'wagon', 'Универсал'
        SUV = 'suv', 'Внедорожник'
        CROSSOVER = 'crossover', 'Кроссовер'
        HATCHBACK = 'hatchback', 'Хэтчбек'
        COUPE = 'coupe', 'Купе'
        MINIVAN = 'minivan', 'Минивэн'

    dealer = models.ForeignKey(
        Dealer, on_delete=models.CASCADE,
        related_name='cars', verbose_name='Автосалон',
    )
    brand = models.CharField('Марка', max_length=50)
    model = models.CharField('Модель', max_length=80)
    year = models.PositiveSmallIntegerField('Год выпуска')
    price = models.PositiveIntegerField('Цена')
    mileage_km = models.PositiveIntegerField('Пробег, км')
    fuel = models.CharField('Топливо', max_length=10, choices=Fuel.choices)
    transmission = models.CharField(
        'Коробка передач', max_length=10, choices=Transmission.choices,
    )
    engine_capacity = models.DecimalField(
        'Объём двигателя, л', max_digits=3, decimal_places=1,
        null=True, blank=True, help_text='Пусто — для электромобилей',
    )
    power_hp = models.PositiveSmallIntegerField('Мощность, л.с.')
    drive = models.CharField('Привод', max_length=3, choices=Drive.choices)
    body = models.CharField('Кузов', max_length=10, choices=Body.choices)
    vin = models.CharField('VIN', max_length=17, blank=True)
    accident = models.BooleanField('Был в ДТП', default=False)
    imported_from = models.CharField(
        'Пригнан из', max_length=50, blank=True,
        help_text='Свободный текст, например: США, Германия, Литва. '
                  'Пусто, если машина не пригнана.',
    )
    negotiable = models.BooleanField('Торг уместен', default=False)
    description = models.TextField('Описание', blank=True)
    internal_note = models.TextField(
        'Внутренняя заметка', blank=True,
        help_text='Видна только в админке, на сайте никогда не показывается.',
    )
    status = models.CharField(
        'Статус', max_length=10,
        choices=Status.choices, default=Status.FOR_SALE,
    )
    sold_at = models.DateTimeField(
        'Дата продажи', null=True, blank=True,
        help_text='Проставляется автоматически, когда статус впервые '
                  'становится «Продано» (в том числе через массовое '
                  'действие «Отметить проданными»). Можно поправить '
                  'вручную, если дата неточная — при повторном сохранении '
                  'уже заполненная дата не перезаписывается сама.',
    )
    video = models.FileField(
        'Видео', upload_to='cars/videos/', blank=True,
        validators=[
            FileExtensionValidator(['mp4', 'mov', 'webm']),
            validate_video_size,
        ],
        help_text=f'mp4, mov или webm, до {MAX_VIDEO_SIZE_MB} МБ.',
    )
    is_published = models.BooleanField(
        'Опубликовано', default=False,
        help_text='Пока не отмечено — машина не видна на сайте, даже '
                  'если сохранена в админке. Отдельно от статуса '
                  '(в продаже/резерв/продан): статус решает, что '
                  'написано на странице, «опубликовано» решает, '
                  'существует ли страница для посетителей вообще.',
    )
    slug = models.SlugField(
        'Адрес страницы (slug)', max_length=150, unique=True, blank=True,
        help_text='Заполняется автоматически, например bmw-530d-2020',
    )
    created_at = models.DateTimeField('Добавлен', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'автомобиль'
        verbose_name_plural = 'Автомобили'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.brand} {self.model} {self.year}'

    def get_absolute_url(self):
        return reverse('cars:car_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f'{self.brand}-{self.model}-{self.year}')
            slug = base
            counter = 2
            while Car.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        # Дата продажи проставляется сама только при первом переходе в
        # «Продано» — если поле уже заполнено (в том числе вручную),
        # повторное сохранение его не трогает. Действие «Отметить
        # проданными» в admin.py делает то же самое отдельно, потому что
        # оно сохраняет через queryset.update() и save() не вызывает.
        if self.status == self.Status.SOLD and self.sold_at is None:
            self.sold_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def main_image(self):
        """Первая фотография (для карточки в каталоге и админке)."""
        return self.images.first()


class CarImage(models.Model):
    """Фотография автомобиля. Главная — та, у которой порядок меньше."""

    car = models.ForeignKey(
        Car, on_delete=models.CASCADE,
        related_name='images', verbose_name='Автомобиль',
    )
    image = models.ImageField('Фото', upload_to='cars/')
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'фотография'
        verbose_name_plural = 'Фотографии'
        ordering = ['order', 'id']

    def __str__(self):
        return f'Фото {self.car} (#{self.order})'


class Booking(models.Model):
    """Заявка клиента на просмотр автомобиля."""

    car = models.ForeignKey(
        Car, on_delete=models.CASCADE,
        related_name='bookings', verbose_name='Автомобиль',
    )
    name = models.CharField('Имя клиента', max_length=100)
    phone = models.CharField('Телефон', max_length=30)
    date = models.DateField('Дата просмотра')
    preferred_time = models.CharField(
        'Желаемое время', max_length=50, blank=True,
        help_text='Например: 15:00 или «после 18:00»',
    )
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    class Meta:
        verbose_name = 'заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} → {self.car} ({self.date})'
