from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render

from . import filters as car_filters
from .models import Car, Dealer


def catalog(request):
    """Main page: dealer header + the car grid, narrowed/sorted by
    whatever filter form fields are present in the URL's query string
    (see cars/filters.py and the form in templates/cars/catalog.html).

    Sold and reserved cars stay in the list (marked with their status) so
    the catalog matches what the dealer actually has on the lot — filters
    narrow within that, they don't hide sold cars on their own.

    Draft (not yet is_published) cars are left out — same rule as
    car_detail's 404 for everyone but staff, just applied to the list
    instead of a single page.
    """
    cars = Car.objects.filter(is_published=True).prefetch_related('images')
    cars, active_filters, sort = car_filters.filter_cars(cars, request.GET)
    # Evaluated once here — the template checks it, counts it, and loops
    # over it, and a QuerySet would otherwise hit the database again for
    # each of those instead of reusing one result set.
    cars = list(cars)

    # Only brands actually present in the (published) catalog — offering
    # one with zero matches would just be a dead end for the visitor.
    brands = sorted(
        set(Car.objects.filter(is_published=True).exclude(brand='').values_list('brand', flat=True)),
        key=str.casefold,
    )

    return render(request, 'cars/catalog.html', {
        'cars': cars,
        'dealer': Dealer.objects.first(),
        'brands': brands,
        'fuel_choices': Car.Fuel.choices,
        'transmission_choices': Car.Transmission.choices,
        'sort_options': car_filters.SORT_OPTIONS,
        'sort': sort,
        'filters': active_filters,
        'active_filter_count': len(active_filters),
    })


def filter_count(request):
    """How many cars the filter fields currently in the form would
    match — same filter_cars() as catalog(), just returns a number
    instead of a page. static/js/filters.js calls this as the visitor
    changes a field, so "Показать N" updates live instead of only
    after they submit the form.
    """
    cars = Car.objects.filter(is_published=True)
    cars, _active_filters, _sort = car_filters.filter_cars(cars, request.GET)
    return JsonResponse({'count': cars.count()})


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
    return render(request, 'cars/car_detail.html', {
        'car': car,
        'dealer': car.dealer,
    })


def privacy(request):
    """Privacy policy. The text itself is the owners' to write."""
    return render(request, 'pages/privacy.html', {'dealer': Dealer.objects.first()})


def terms(request):
    """Terms of use. The text itself is the owners' to write."""
    return render(request, 'pages/terms.html', {'dealer': Dealer.objects.first()})
