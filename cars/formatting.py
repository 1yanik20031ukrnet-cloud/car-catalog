"""Shared display formatting for prices, numbers and Russian plurals.

Kept out of the template tags so the admin and any future code (Telegram
notifications, exports) can format a price exactly the way the site does.
"""

# Digits and the currency symbol must never be split across a line break.
NBSP = ' '


def group_digits(value):
    """38900 -> '38 900'. Returns the value untouched if it is not a number."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return value
    return f'{number:,}'.replace(',', NBSP)


def format_price(price, currency=''):
    """38900, '$' -> '38 900 $'.

    The symbol goes after the number for every currency the Dealer model
    offers: that is the usual order for ₴ and zł, and it keeps the catalog,
    the car page and the admin list showing one and the same price.
    """
    number = group_digits(price)
    if not currency:
        return number
    return f'{number}{NBSP}{currency}'


def plural_ru(value, one, few, many):
    """Pick the Russian plural form: 1 машина, 3 машины, 16 машин.

    Django's built-in `pluralize` only holds two forms and silently returns
    an empty string when given three, so Russian needs its own rule.
    """
    try:
        number = abs(int(value))
    except (TypeError, ValueError):
        return many
    if number % 100 in range(11, 15):
        return many
    last = number % 10
    if last == 1:
        return one
    if last in (2, 3, 4):
        return few
    return many
