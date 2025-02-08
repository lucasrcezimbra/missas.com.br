from django import template
from django.template.defaultfilters import register

register = template.Library()


@register.filter(name="group_by_day")
def group_by_day(schedules):
    """Group schedules by day."""
    if not schedules:
        return []
    from itertools import groupby

    return [
        (day, list(items))
        for day, items in groupby(
            sorted(schedules, key=lambda x: x.day), key=lambda x: x.day
        )
    ]
