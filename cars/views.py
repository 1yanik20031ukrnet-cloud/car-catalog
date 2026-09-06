from django.core.cache import cache
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from . import filters as car_filters
from .forms import BookingForm
from .models import Car, Dealer

# Простая защита от спама поверх honeypot-поля в самой форме: с одного
# IP — не чаще одной заявки в этот промежуток, неважно на какую машину.
# Через cache (по умолчанию — LocMemCache, ничего дополнительно
# настраивать не нужно). На нескольких процессах/серверах счётчик не
# общий — для одного сайта на одном сервере этого достаточно, если
# станет мало — тогда переходить на Redis и т.п.
BOOKING_THROTTLE_SECONDS = 60


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

    # A sold car doesn't take new viewing requests — the form below just
    # isn't offered for one (see the template), so a POST for a sold car
    # only happens if someone crafts the request by hand; still validated
    # normally rather than trusted blindly.
    if request.method == 'POST' and car.status != Car.Status.SOLD:
        booking_form = BookingForm(request.POST)
        throttle_key = f'booking-throttle-{request.META.get("REMOTE_ADDR")}'
        if cache.get(throttle_key):
            booking_form.add_error(
                None, 'Слишком много заявок подряд — подождите минуту и попробуйте снова.',
            )
        elif booking_form.is_valid():
            booking = booking_form.save(commit=False)
            booking.car = car
            booking.save()
            cache.set(throttle_key, True, BOOKING_THROTTLE_SECONDS)
            # Redirect-after-POST so refreshing the result page never
            # re-submits the same booking a second time.
            return redirect(f'{car.get_absolute_url()}?booked=1')
    else:
        booking_form = BookingForm()

    return render(request, 'cars/car_detail.html', {
        'car': car,
        'dealer': car.dealer,
        'booking_form': booking_form,
        'booking_success': request.GET.get('booked') == '1',
    })


def privacy(request):
    """Privacy policy. The text itself is the owners' to write."""
    return render(request, 'pages/privacy.html', {'dealer': Dealer.objects.first()})


def terms(request):
    """Terms of use. The text itself is the owners' to write."""
    return render(request, 'pages/terms.html', {'dealer': Dealer.objects.first()})
