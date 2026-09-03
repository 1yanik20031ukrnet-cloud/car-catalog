"""Catalog filtering & sorting — GET params in, a narrowed queryset out.

Plain Django ORM filters, no separate filtering library: the catalog is a
few dozen cars at most, this is instant, and it's easy to read top to
bottom. See cars/views.py:catalog for how this plugs in, and
templates/cars/catalog.html for the form that produces these params.
"""

SORT_OPTIONS = {
    'new': ('-created_at', 'Сначала новые'),
    'price_asc': ('price', 'Сначала дешевле'),
    'price_desc': ('-price', 'Сначала дороже'),
}
DEFAULT_SORT = 'new'


def _parse_int(value):
    """A stray/garbage value is treated the same as "not set" — a broken
    filter link should show everything, not a crash page."""
    if not value:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def filter_cars(queryset, params):
    """Narrows `queryset` by whatever's present in `params` (request.GET).

    Returns (queryset, active, sort):
    - active: dict of only the filters that were actually applied, in
      plain form-field terms — used to re-fill the form and to count
      "Фильтры (N)".
    - sort: the resolved sort key (falls back to DEFAULT_SORT for a
      missing/unknown value), used to re-select the sort dropdown and to
      order the queryset.
    """
    active = {}

    brand = params.get('brand', '').strip()
    if brand:
        queryset = queryset.filter(brand=brand)
        active['brand'] = brand

    model = params.get('model', '').strip()
    if model:
        queryset = queryset.filter(model__icontains=model)
        active['model'] = model

    price_min = _parse_int(params.get('price_min'))
    if price_min is not None:
        queryset = queryset.filter(price__gte=price_min)
        active['price_min'] = price_min

    price_max = _parse_int(params.get('price_max'))
    if price_max is not None:
        queryset = queryset.filter(price__lte=price_max)
        active['price_max'] = price_max

    year_min = _parse_int(params.get('year_min'))
    if year_min is not None:
        queryset = queryset.filter(year__gte=year_min)
        active['year_min'] = year_min

    year_max = _parse_int(params.get('year_max'))
    if year_max is not None:
        queryset = queryset.filter(year__lte=year_max)
        active['year_max'] = year_max

    mileage_max = _parse_int(params.get('mileage_max'))
    if mileage_max is not None:
        queryset = queryset.filter(mileage_km__lte=mileage_max)
        active['mileage_max'] = mileage_max

    fuel = params.get('fuel', '').strip()
    if fuel:
        queryset = queryset.filter(fuel=fuel)
        active['fuel'] = fuel

    transmission = params.get('transmission', '').strip()
    if transmission:
        queryset = queryset.filter(transmission=transmission)
        active['transmission'] = transmission

    sort = params.get('sort')
    if sort not in SORT_OPTIONS:
        sort = DEFAULT_SORT
    order_by, _label = SORT_OPTIONS[sort]
    queryset = queryset.order_by(order_by)

    return queryset, active, sort
