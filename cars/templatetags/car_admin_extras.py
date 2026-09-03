from datetime import timedelta

from django import template
from django.db.models import Count
from django.utils import timezone

from cars.models import Car

register = template.Library()


def _month_starts(count, today):
    """`count` first-of-month dates ending at today's month, oldest first.

    Plain datetime arithmetic — no dateutil dependency for something
    this small: go to day=1 of the current month, then repeatedly step
    back one day and snap to day=1 again to reach the previous month.
    """
    starts = []
    current = today.replace(day=1)
    for _ in range(count):
        starts.append(current)
        current = (current - timedelta(days=1)).replace(day=1)
    return list(reversed(starts))


def _status_counts():
    """Total + per-status counts — shared by the full dashboard and the
    compact sidebar widget so there's one query for this, not two."""
    counts = dict(Car.objects.values_list('status').annotate(count=Count('id')))
    return {
        'total': sum(counts.values()),
        'for_sale': counts.get(Car.Status.FOR_SALE, 0),
        'reserved': counts.get(Car.Status.RESERVED, 0),
        'sold': counts.get(Car.Status.SOLD, 0),
    }


@register.inclusion_tag('cars/admin_sidebar_stats.html')
def car_stats_sidebar():
    """Compact version of the same counts for the sidebar — visible on
    every admin page, not just the main one, without repeating the
    heavier per-period/chart queries the full dashboard needs."""
    return _status_counts()


@register.inclusion_tag('cars/admin_stats.html')
def car_stats_dashboard():
    """Small MVP dashboard for the admin's main page.

    Everything here is a handful of plain queries against the Car
    table — no separate analytics app, no scheduled aggregation. For a
    catalog of a few dozen cars this is instant, and it stays correct
    automatically as cars are added/sold, unlike a hand-kept counter.
    """
    now = timezone.localtime(timezone.now())
    month_start = now.replace(hour=0, minute=0, second=0, microsecond=0, day=1)
    last_30_days_start = now - timedelta(days=30)

    status_counts = _status_counts()
    sold_qs = Car.objects.filter(status=Car.Status.SOLD)

    # Cars sold before sold_at existed (or marked sold before this
    # feature) have sold_at = NULL — they still count in "продано
    # всего" above (that's a plain status count), but there is no
    # reliable date to place them in a period, so period counts and
    # the chart only include cars that do have one.
    sold_with_date = sold_qs.filter(sold_at__isnull=False)

    month_starts = _month_starts(6, now)
    chart_data = []
    max_count = 0
    for i, start in enumerate(month_starts):
        end = month_starts[i + 1] if i + 1 < len(month_starts) else now
        count = sold_with_date.filter(sold_at__gte=start, sold_at__lt=end).count()
        max_count = max(max_count, count)
        chart_data.append({'label': start.strftime('%m.%Y'), 'count': count})
    for item in chart_data:
        item['height_pct'] = round(item['count'] / max_count * 100) if max_count else 0

    return {
        **status_counts,
        'sold_this_month': sold_with_date.filter(sold_at__gte=month_start).count(),
        'sold_last_30_days': sold_with_date.filter(sold_at__gte=last_30_days_start).count(),
        'sold_all_time': status_counts['sold'],
        'chart_data': chart_data,
        'has_undated_sales': sold_qs.filter(sold_at__isnull=True).exists(),
    }
