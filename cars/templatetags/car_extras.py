from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static

from cars import formatting

register = template.Library()


@register.filter
def spaced(value):
    """Group digits by three: 117000 -> '117 000'. Used for mileage."""
    return formatting.group_digits(value)


@register.filter
def money(price, currency=''):
    """Format a price with the dealer's currency: '38 900 $'."""
    return formatting.format_price(price, currency)


@register.filter
def plural_ru(value, forms):
    """Pick a Russian plural form.

    Usage: {{ n|plural_ru:'автомобиль,автомобиля,автомобилей' }} — three
    comma-separated forms, unlike Django's `pluralize`, which holds two and
    renders nothing at all when given three.
    """
    parts = [part.strip() for part in forms.split(',')]
    if len(parts) != 3:
        return ''
    return formatting.plural_ru(value, *parts)


@register.simple_tag
def versioned_static(path):
    """Same as {% static %}, but with a ?v=<file's mtime> query string.

    Without this, a browser can keep serving a stale cached copy of a
    CSS/JS file after it's edited — even on a normal reload — since the
    URL never changes. Bit the owner more than once (site style.css,
    admin's admin-overrides.css) before this existed there too.
    """
    url = static(path)
    try:
        mtime = int((Path(settings.BASE_DIR) / 'static' / path).stat().st_mtime)
    except OSError:
        return url
    return f'{url}?v={mtime}'
