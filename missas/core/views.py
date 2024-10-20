from datetime import datetime, time, timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render, resolve_url

from missas.core.models import City, Schedule, State


def index(request):
    now = datetime.utcnow() - timedelta(hours=3)
    weekday = ("segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo")[
        now.weekday()
    ]  # TODO: encapsulate this logic
    return redirect(
        resolve_url("by_city", state="rio-grande-do-norte", city="natal")
        + f"?dia={weekday}"
        + f"&horario={now.hour}"
    )


def cities_by_state(request, state):
    state = get_object_or_404(State, slug=state)
    cities = (
        state.cities.annotate_has_schedules().order_by("-has_schedules", "name").all()
    )
    return render(
        request, "cities_by_state.html", context={"state": state, "cities": cities}
    )


# @vary_on_headers("HX-Request")  # TODO: Cloudflare ignores Vary header
def by_city(request, state, city):
    city = get_object_or_404(City, slug=city, state__slug=state)
    day_name = request.GET.get("dia")
    hour = request.GET.get("horario")
    type_name = request.GET.get("tipo")
    verified_only = request.GET.get("verificado") == "1"
    day = {
        "domingo": Schedule.Day.SUNDAY,
        "segunda": Schedule.Day.MONDAY,
        "terca": Schedule.Day.TUESDAY,
        "quarta": Schedule.Day.WEDNESDAY,
        "quinta": Schedule.Day.THURSDAY,
        "sexta": Schedule.Day.FRIDAY,
        "sabado": Schedule.Day.SATURDAY,
    }.get(day_name)
    type = {
        "missas": Schedule.Type.MASS,
        "confissoes": Schedule.Type.CONFESSION,
    }.get(type_name, Schedule.Type.MASS)
    schedules = Schedule.objects.filter(parish__city=city, type=type)

    if day is not None:
        schedules = schedules.filter(day=day)

    if hour is not None:
        hour = time(int(hour))
        qs = Q(start_time__gte=hour) | Q(end_time__gte=hour)
        schedules = schedules.filter(qs)

    if verified_only:
        schedules = schedules.filter(verified_at__isnull=False)

    schedules = schedules.order_by("day", "start_time")

    return render(
        request,
        "cards.html" if request.htmx else "parishes_by_city.html",
        {
            "schedules": schedules,
            "day": day,
            "city": city,
            "hour": hour.hour if hour else 0,
            "type": type,
            "Schedule": Schedule,
        },
    )
