from django.http import Http404
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

    An unpublished (draft) car also 404s for everyone except staff —
    that's what lets "Просмотр на сайте" in the admin work as a real
    preview: logged-in staff can open the page before it's public,
    a regular visitor gets 404 for the same link until it's published.
    """
    car = get_object_or_404(
        Car.objects.select_related('dealer').prefetch_related('images'),
        slug=slug,
    )
    if not car.is_published and not request.user.is_staff:
        raise Http404('Автомобиль ещё не опубликован')
    return render(request, 'cars/car_detail.html', {'car': car})
