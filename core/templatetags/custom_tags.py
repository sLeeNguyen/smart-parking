from django import template
from django.utils import timezone

from core.utils import client_timezone

register = template.Library()


@register.filter()
def to_int(value):
    return int(value)


@register.filter()
def duration_format(d1, d2):
    d = d1 - d2
    if d and isinstance(d, timezone.timedelta):
        total_seconds = d.total_seconds()
        if total_seconds > 0:
            hours = int(total_seconds / 3600)
            minutes = int(total_seconds - hours*3600) // 60
            seconds = int(total_seconds) % 60

            hours = str(hours)
            minutes = str(minutes)
            seconds = str(seconds)
            if len(hours) < 2:
                hours = '0' + hours
            if len(minutes) < 2:
                minutes = '0' + minutes
            if len(seconds) < 2:
                seconds = '0' + seconds
            return "%s:%s:%s" % (hours, minutes, seconds)
    return 'None'


@register.filter()
def datetime_format(date, client_tz=None):
    if date:
        date = client_timezone(date, client_tz)
        return date.strftime("%d/%m/%Y %H:%M:%S")
    return ''
