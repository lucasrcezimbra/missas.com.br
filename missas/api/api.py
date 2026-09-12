from datetime import date, time

from django.db.models import Prefetch
from ninja import NinjaAPI, Schema
from ninja.pagination import LimitOffsetPagination, paginate

from missas.api.models import WhatsAppParish
from missas.core.models import Schedule


class ContactOut(Schema):
    id: int
    whatsapp: str


class SourceOut(Schema):
    id: int
    type: str
    description: str
    link: str | None


class LocationOut(Schema):
    id: int
    name: str
    address: str


class ScheduleOut(Schema):
    id: int
    day: int
    start_time: time
    end_time: time | None
    observation: str
    verified_at: date | None
    location_name: str
    location: LocationOut | None
    source: SourceOut | None


class ParishOut(Schema):
    id: int
    name: str
    city: str
    state: str
    contact: ContactOut
    mass_schedules: list[ScheduleOut]

    @staticmethod
    def resolve_city(obj):
        return obj.city.name

    @staticmethod
    def resolve_state(obj):
        return obj.city.state.short_name


api = NinjaAPI(docs_url=None, openapi_url=None)


@api.get("/parishes", response=list[ParishOut])
@paginate(LimitOffsetPagination, max_limit=100)
def parishes(request):
    schedules = (
        Schedule.objects.filter(type=Schedule.Type.MASS)
        .select_related("source", "location")
        .order_by("day", "start_time", "pk")
    )
    return (
        WhatsAppParish.objects.for_api()
        .select_related("city__state", "contact")
        .prefetch_related(
            Prefetch("schedules", queryset=schedules, to_attr="mass_schedules")
        )
    )
