from django.db import models
from django.utils.text import slugify


class Dealer(models.Model):
    """Автосалон. Пока одна запись, но структура готова к нескольким."""

    class Currency(models.TextChoices):
        UAH = '₴', '₴ (гривна)'
        USD = '$', '$ (доллар)'
        EUR = '€', '€ (евро)'
        PLN = 'zł', 'zł (злотый)'

    name = models.CharField('Название', max_length=100)
    description = models.TextField('Короткое описание', blank=True)
    phone = models.CharField('Телефон', max_length=30)
    instagram = models.URLField('Ссылка на Instagram', blank=True)
    telegram = models.CharField('Telegram (@username)', max_length=100, blank=True)
    whatsapp = models.CharField('WhatsApp (номер)', max_length=30, blank=True)
    currency = models.CharField(
        'Валюта цен', max_length=3,
        choices=Currency.choices, default=Currency.USD,
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
    description = models.TextField('Описание', blank=True)
    status = models.CharField(
        'Статус', max_length=10,
        choices=Status.choices, default=Status.FOR_SALE,
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

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f'{self.brand}-{self.model}-{self.year}')
            slug = base
            counter = 2
            while Car.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
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
