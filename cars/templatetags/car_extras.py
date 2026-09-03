from django import template

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
