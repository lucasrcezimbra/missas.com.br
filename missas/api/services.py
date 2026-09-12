import hashlib

from django.core import signing
from django.db import transaction
from django.db.models import Prefetch

from missas.api.models import WhatsAppParish
from missas.core.models import Schedule


class ParishListChanged(Exception):
    pass


@transaction.atomic
def parish_page(limit, cursor):
    position = (
        signing.loads(cursor, salt="missas.api.parishes.v1", max_age=3600)
        if cursor is not None
        else None
    )
    members = hashlib.sha256()
    for pk in WhatsAppParish.objects.for_api().values_list("pk", flat=True).iterator():
        members.update(f"{pk},".encode())
    membership = members.hexdigest()
    if position is not None and position["membership"] != membership:
        raise ParishListChanged()
    after = position["after"] if position is not None else 0
    schedules = (
        Schedule.objects.filter(type=Schedule.Type.MASS)
        .select_related("source", "location")
        .order_by("day", "start_time", "pk")
    )
    parishes = (
        WhatsAppParish.objects.for_api()
        .select_related("city__state", "contact")
        .prefetch_related(
            Prefetch("schedules", queryset=schedules, to_attr="mass_schedules")
        )
    )
    page = list(parishes.filter(pk__gt=after)[: limit + 1])
    has_next = len(page) > limit
    page = page[:limit]
    return {
        "items": [
            {
                "id": parish.pk,
                "name": parish.name,
                "city": parish.city.name,
                "state": parish.city.state.short_name,
                "contact": parish.contact,
                "mass_schedules": parish.mass_schedules,
            }
            for parish in page
        ],
        "next_cursor": (
            signing.dumps(
                {"after": page[-1].pk, "membership": membership},
                salt="missas.api.parishes.v1",
            )
            if has_next
            else None
        ),
    }
