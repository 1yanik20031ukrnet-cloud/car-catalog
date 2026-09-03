"""Fill the database with a demo dealer and demo cars.

Usage: python manage.py seed_demo
Placeholder photos are generated locally with Pillow (no downloads).
"""

from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont

from cars.models import Car, CarImage, Dealer

# brand, model, year, price $, mileage, fuel, transmission,
# engine, hp, drive, body, status
DEMO_CARS = [
    ('BMW', '530d', 2020, 33900, 112000, 'diesel', 'automatic', '3.0', 265, 'rwd', 'sedan', 'for_sale'),
    ('BMW', 'X5 xDrive30d', 2019, 42500, 98000, 'diesel', 'automatic', '3.0', 249, 'awd', 'suv', 'for_sale'),
    ('BMW', '320i', 2018, 21900, 134000, 'petrol', 'automatic', '2.0', 184, 'rwd', 'sedan', 'for_sale'),
    ('Audi', 'A6 45 TDI', 2021, 39800, 74000, 'diesel', 'automatic', '3.0', 231, 'awd', 'sedan', 'for_sale'),
    ('Audi', 'Q7 50 TDI', 2019, 44900, 105000, 'diesel', 'automatic', '3.0', 286, 'awd', 'suv', 'reserved'),
    ('Audi', 'A4 2.0 TFSI', 2017, 18500, 148000, 'petrol', 'automatic', '2.0', 190, 'fwd', 'sedan', 'for_sale'),
    ('Mercedes-Benz', 'E 220 d', 2020, 36700, 89000, 'diesel', 'automatic', '2.0', 194, 'rwd', 'sedan', 'for_sale'),
    ('Mercedes-Benz', 'GLC 300', 2021, 46900, 61000, 'petrol', 'automatic', '2.0', 258, 'awd', 'crossover', 'for_sale'),
    ('Mercedes-Benz', 'C 200', 2018, 23400, 121000, 'petrol', 'automatic', '2.0', 184, 'rwd', 'sedan', 'sold'),
    ('Volkswagen', 'Passat 2.0 TDI', 2019, 19900, 143000, 'diesel', 'automatic', '2.0', 150, 'fwd', 'wagon', 'for_sale'),
    ('Volkswagen', 'Tiguan 2.0 TSI', 2020, 26800, 87000, 'petrol', 'automatic', '2.0', 180, 'awd', 'crossover', 'for_sale'),
    ('Volkswagen', 'Golf 1.4 TSI', 2017, 13900, 156000, 'petrol', 'manual', '1.4', 125, 'fwd', 'hatchback', 'for_sale'),
    ('Porsche', 'Macan S', 2019, 52900, 79000, 'petrol', 'automatic', '3.0', 354, 'awd', 'crossover', 'for_sale'),
    ('Porsche', 'Cayenne', 2020, 74500, 58000, 'petrol', 'automatic', '3.0', 340, 'awd', 'suv', 'for_sale'),
    ('Volvo', 'XC60 B4', 2020, 34900, 92000, 'diesel', 'automatic', '2.0', 197, 'awd', 'crossover', 'for_sale'),
    ('Volvo', 'XC90 T8', 2018, 38900, 117000, 'hybrid', 'automatic', '2.0', 390, 'awd', 'suv', 'for_sale'),
]

# Two-color gradients per photo, so cars look different from each other.
GRADIENTS = [
    ((28, 32, 44), (94, 114, 155)),
    ((40, 26, 26), (158, 98, 82)),
    ((24, 40, 34), (96, 148, 122)),
    ((36, 30, 48), (132, 104, 170)),
    ((30, 30, 30), (140, 140, 140)),
]

DESCRIPTION = (
    'Автомобиль в отличном состоянии, полностью обслужен. '
    'Пригнан из Европы, проверен на СТО. Возможен обмен. '
    'Звоните или пишите в мессенджер — ответим быстро.'
)


def make_placeholder(title, subtitle, gradient):
    """Generate an 800x600 gradient JPEG with the car name on it."""
    width, height = 800, 600
    top, bottom = gradient
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        k = y / height
        color = tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)
    font_big = ImageFont.load_default(size=52)
    font_small = ImageFont.load_default(size=30)
    draw.text((40, 250), title, font=font_big, fill=(255, 255, 255))
    draw.text((40, 320), subtitle, font=font_small, fill=(220, 220, 220))
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=80)
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = 'Создаёт демо-автосалон и демо-автомобили с фото-заглушками'

    def handle(self, *args, **options):
        if Car.objects.exists():
            self.stdout.write(self.style.WARNING(
                'В базе уже есть автомобили — ничего не делаю. '
                'Чтобы пересоздать демо-данные, удалите их в админке.'
            ))
            return

        dealer, _ = Dealer.objects.get_or_create(
            name='Premium Cars',
            defaults={
                'description': 'Проверенные автомобили из Европы. Киев.',
                'phone': '+380 67 000 00 00',
                'instagram': 'https://instagram.com/premiumcars.demo',
                'telegram': '@premiumcars_demo',
                'currency': Dealer.Currency.USD,
            },
        )

        for index, row in enumerate(DEMO_CARS):
            (brand, model, year, price, mileage, fuel, transmission,
             engine, hp, drive, body, status) = row
            car = Car.objects.create(
                dealer=dealer,
                brand=brand,
                model=model,
                year=year,
                price=price,
                mileage_km=mileage,
                fuel=fuel,
                transmission=transmission,
                engine_capacity=engine,
                power_hp=hp,
                drive=drive,
                body=body,
                status=status,
                description=DESCRIPTION,
                is_published=True,
            )
            for photo_number in range(3):
                gradient = GRADIENTS[(index + photo_number) % len(GRADIENTS)]
                content = make_placeholder(
                    f'{brand} {model}',
                    f'{year} · photo {photo_number + 1}',
                    gradient,
                )
                car_image = CarImage(car=car, order=photo_number)
                car_image.image.save(f'{car.slug}-{photo_number + 1}.jpg', content)
            self.stdout.write(f'  + {car}')

        self.stdout.write(self.style.SUCCESS(
            f'Готово: {Car.objects.count()} автомобилей у салона «{dealer}».'
        ))
