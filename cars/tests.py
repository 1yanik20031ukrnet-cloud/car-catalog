from django.test import SimpleTestCase

from cars.formatting import NBSP, format_price, group_digits, plural_ru

FORMS = ('автомобиль', 'автомобиля', 'автомобилей')


class PluralRuTests(SimpleTestCase):
    """Django's own `pluralize` holds two forms and silently renders nothing
    when given three, which once dropped the noun from the catalog heading."""

    def test_picks_the_form_by_the_last_digit(self):
        cases = {
            1: 'автомобиль', 2: 'автомобиля', 4: 'автомобиля',
            5: 'автомобилей', 16: 'автомобилей', 21: 'автомобиль',
            22: 'автомобиля', 25: 'автомобилей', 101: 'автомобиль',
        }
        for number, expected in cases.items():
            with self.subTest(number=number):
                self.assertEqual(plural_ru(number, *FORMS), expected)

    def test_eleven_to_fourteen_are_exceptions(self):
        for number in (11, 12, 13, 14, 111, 112):
            with self.subTest(number=number):
                self.assertEqual(plural_ru(number, *FORMS), 'автомобилей')

    def test_zero_and_junk_fall_back_to_the_many_form(self):
        self.assertEqual(plural_ru(0, *FORMS), 'автомобилей')
        self.assertEqual(plural_ru(None, *FORMS), 'автомобилей')


class PriceTests(SimpleTestCase):
    def test_digits_are_grouped_with_a_non_breaking_space(self):
        self.assertEqual(group_digits(117000), f'117{NBSP}000')
        self.assertEqual(group_digits(900), '900')

    def test_currency_follows_the_number(self):
        self.assertEqual(format_price(38900, '$'), f'38{NBSP}900{NBSP}$')
        self.assertEqual(format_price(38900, 'zł'), f'38{NBSP}900{NBSP}zł')

    def test_missing_currency_leaves_the_bare_number(self):
        self.assertEqual(format_price(38900), f'38{NBSP}900')

    def test_non_numeric_value_passes_through(self):
        self.assertEqual(group_digits(''), '')
        self.assertEqual(group_digits(None), None)
