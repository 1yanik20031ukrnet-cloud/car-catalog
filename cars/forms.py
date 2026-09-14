import datetime
import re

from django import forms
from django.utils import timezone

from .models import Booking

# Часы работы салона для записи на просмотр. Пока просто константы —
# не поле у Dealer, потому что владелец сам сказал "давай пока
# возьмём" — если позже это должно различаться по салонам, вынести в
# модель Dealer будет несложно (описание в TASKS.md).
BOOKING_HOURS_START = datetime.time(8, 0)
BOOKING_HOURS_END = datetime.time(20, 0)
BOOKING_TIME_STEP_MINUTES = 15

# Что подставляется в форму, пока посетитель ничего не выбрал
# (2026-09-14, по просьбе владельца). Смысл: пустая форма — лишний шаг;
# человеку проще поправить готовое время, чем выбрать его с нуля.
# Заявка без времени раньше проходила насквозь, теперь время
# обязательно — поэтому значение по умолчанию должно быть разумным.
BOOKING_DEFAULT_TIME = datetime.time(9, 0)
# Завтра, а не сегодня: салону нужно время перезвонить и подтвердить,
# а «сегодня через час» чаще всего нереалистично.
BOOKING_DEFAULT_DAYS_AHEAD = 1


def _hour_choices():
    """Каждый рабочий час, "08".."20"."""
    return [
        (f'{h:02d}', f'{h:02d}') for h in range(BOOKING_HOURS_START.hour, BOOKING_HOURS_END.hour + 1)
    ]


def _minute_choices():
    """Минуты с шагом BOOKING_TIME_STEP_MINUTES, "00".."45"."""
    return [
        (f'{m:02d}', f'{m:02d}') for m in range(0, 60, BOOKING_TIME_STEP_MINUTES)
    ]


def default_booking_date():
    return timezone.localdate() + datetime.timedelta(days=BOOKING_DEFAULT_DAYS_AHEAD)


class BookingForm(forms.ModelForm):
    """Записаться на просмотр конкретного автомобиля.

    `car` не входит в форму — его подставляет view из URL, посетитель
    его не выбирает и не может подменить.
    """

    # Два отдельных <select> (час / минуты) вместо одного списка
    # "08:00", "08:15", ... — по просьбе владельца, чтобы визуально
    # было похоже на пару "от–до" у цены/года в фильтрах каталога, а
    # не один длинный список. `preferred_time` (сохраняется в базу)
    # собирается из этих двух в save() ниже — модельного поля для
    # него в форме больше нет, поэтому в Meta.fields его тоже нет.
    #
    # Раньше здесь был <input type="time"> с min/max/step — но у
    # нативного пикера времени в браузере step/min/max влияют только
    # на шаг стрелочек и на валидность при отправке, а сам выпадающий
    # список часов и минут показывается целиком, без ограничений (это
    # особенность самого HTML, не баг) — реально можно было прокрутить
    # и выбрать время вне рабочих часов. Обычные <select> с готовым
    # списком физически не дают выбрать ничего другого.
    #
    # Оба поля обязательны и заполнены заранее (2026-09-14). Раньше они
    # были необязательными, и заявка спокойно уходила вообще без
    # времени — салон получал «приеду посмотреть» без часа.
    # Пустых вариантов «Час»/«Мин» в списках больше нет: выбрать
    # «ничего» физически нельзя, поэтому и проверять этот случай не
    # нужно.
    preferred_hour = forms.ChoiceField(
        label='Час', choices=_hour_choices,
        initial=f'{BOOKING_DEFAULT_TIME.hour:02d}',
        widget=forms.Select(attrs={'class': 'chip-field chip-field--select'}),
    )
    preferred_minute = forms.ChoiceField(
        label='Минуты', choices=_minute_choices,
        initial=f'{BOOKING_DEFAULT_TIME.minute:02d}',
        widget=forms.Select(attrs={'class': 'chip-field chip-field--select'}),
    )

    # Honeypot против спам-ботов: обычное текстовое поле (не
    # type="hidden" — его несложные боты умеют пропускать), спрятанное
    # за пределами экрана через CSS (.booking-form__honeypot в
    # style.css). Человек его никогда не видит и не заполняет; бот,
    # который слепо заполняет все найденные поля формы, — заполнит.
    # Если оно не пустое — считаем заявку спамом.
    website = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'class': 'booking-form__honeypot',
            'tabindex': '-1',
            'autocomplete': 'off',
            'aria-hidden': 'true',
        }),
    )

    class Meta:
        model = Booking
        # preferred_time не здесь — собирается в save() из
        # preferred_hour/preferred_minute, объявленных выше.
        fields = ['name', 'phone', 'date', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'chip-field', 'placeholder': 'Иван Иванов'}),
            'phone': forms.TextInput(attrs={
                'class': 'chip-field', 'type': 'tel', 'placeholder': '+380 XX XXX XX XX',
            }),
            # min не даёт выбрать прошедший день прямо в календаре —
            # clean_date() всё равно проверяет это на сервере, но
            # приятнее не давать ошибиться, чем ругаться после отправки.
            #
            # format обязателен. У проекта LANGUAGE_CODE='ru', и без
            # него Django подставляет дату по-русски — value="15.09.2026".
            # <input type="date"> понимает только ISO (ГГГГ-ММ-ДД) и
            # любое другое значение молча выбрасывает, из-за чего поле
            # выглядит пустым, хотя дата в форму передана.
            'date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'chip-field', 'type': 'date'},
            ),
            'comment': forms.Textarea(attrs={
                'class': 'chip-field chip-field--textarea',
                'rows': 3,
                'placeholder': 'Необязательно',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Дата по умолчанию — завтра, и календарь не предлагает прошлое.
        # Ставится здесь, а не в поле модели: значение зависит от того,
        # какой сегодня день, то есть считается при каждом показе формы.
        #
        # Именно в self.initial, а не в self.fields['date'].initial:
        # ModelForm заполняет self.initial из самого объекта, и для
        # новой заявки туда попадает date=None, который перебивает
        # значение по умолчанию у поля — дата так и осталась бы пустой.
        if not self.initial.get('date'):
            self.initial['date'] = default_booking_date()
        self.fields['date'].widget.attrs['min'] = timezone.localdate().isoformat()

    def clean(self):
        cleaned = super().clean()
        hour = cleaned.get('preferred_hour')
        minute = cleaned.get('preferred_minute')
        # Рабочий день заканчивается ровно в BOOKING_HOURS_END —
        # "20:30" уже нерабочее время, хотя оба select'а сами по себе
        # предлагают только допустимые часы/минуты по отдельности.
        if hour and minute:
            if hour == f'{BOOKING_HOURS_END.hour:02d}' and minute != '00':
                self.add_error(
                    'preferred_minute',
                    f'Салон закрывается в {BOOKING_HOURS_END:%H:%M} — выберите время раньше.',
                )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        hour = self.cleaned_data['preferred_hour']
        minute = self.cleaned_data['preferred_minute']
        instance.preferred_time = f'{hour}:{minute}'
        if commit:
            instance.save()
        return instance

    def clean_website(self):
        if self.cleaned_data.get('website'):
            # Сообщение никто из настоящих посетителей не увидит —
            # поле для них невидимо, до этой ошибки дело не доходит.
            raise forms.ValidationError('Похоже на спам.')
        return self.cleaned_data.get('website')

    def clean_date(self):
        date = self.cleaned_data['date']
        if date < timezone.localdate():
            raise forms.ValidationError('Дата не может быть в прошлом.')
        return date

    def clean_phone(self):
        """Не строгий формат конкретной страны (салон должен подойти
        не только Украине) — просто проверка, что цифр введено похоже
        на настоящий номер целиком, а не половина или явный мусор."""
        phone = self.cleaned_data['phone']
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 9:
            raise forms.ValidationError('Введите номер телефона полностью.')
        if len(digits) > 15:
            raise forms.ValidationError('Слишком длинный номер телефона.')
        return phone
