from django.shortcuts import get_object_or_404, render

from .models import Car


def catalog(request):
    """Main page: dealer header + car catalog (cars will appear in stage 2-3)."""
    return render(request, 'cars/catalog.html')


def car_detail(request, slug):
    """One car's page: photos, specs, description, contact/booking CTAs.

    A sold or reserved car is still shown (with its status), so an old
    link from Instagram/Telegram never breaks — only a truly missing
    or removed car gives 404.
    """
    car = get_object_or_404(
        Car.objects.select_related('dealer').prefetch_related('images'),
        slug=slug,
    )
    return render(request, 'cars/car_detail.html', {'car': car})
