from datetime import time
from math import asin, cos, radians, sin, sqrt

from django.db import models
from django.db.models import Q
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from missas.core.models import City, ContactRequest, Parish, Schedule, State


def index(request):
    stats = {
        "cities_with_parishes": City.objects.filter_with_schedule().count(),
        "parishes": Parish.objects.count(),
        "schedules": Schedule.objects.count(),
        "verified_schedules": Schedule.objects.filter_verified().count(),
    }

    states_with_cities = (
        State.objects.prefetch_related(
            models.Prefetch(
                "cities",
                queryset=City.objects.filter_with_schedule().order_by("name"),
                to_attr="cities_with_parishes",
            )
        )
        .filter(cities__parishes__schedules__isnull=False)
        .distinct()
        .order_by("name")
    )

    return render(
        request,
        "home.html",
        {
            "stats": stats,
            "states_with_cities": states_with_cities,
        },
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
    schedules = schedules.select_related(
        "parish", "parish__city", "parish__city__state", "source", "location"
    ).prefetch_related("parish__contact")
    template = (
        "cards.html"
        if request.htmx and not request.htmx.boosted
        else "parishes_by_city.html"
    )

    return render(
        request,
        template,
        {
            "schedules": schedules,
            "day": day,
            "city": city,
            "hour": hour.hour if hour else 0,
            "type": type,
            "Schedule": Schedule,
        },
    )


def parish_detail(request, state, city, parish):
    parish = get_object_or_404(
        Parish, slug=parish, city__slug=city, city__state__slug=state
    )
    schedules = (
        Schedule.objects.filter(parish=parish)
        .order_by("type", "day", "start_time")
        .prefetch_related("source")
    )

    return render(
        request,
        "parish_detail.html",
        {
            "parish": parish,
            "schedules": schedules,
            "Schedule": Schedule,
        },
    )


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in kilometers between two points on Earth."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return km


def nearby_schedules(request):
    if request.method == "POST":
        try:
            user_lat = float(request.POST.get("lat"))
            user_lon = float(request.POST.get("long"))
        except (TypeError, ValueError):
            return render(
                request,
                "parishes_by_city.html",
                {
                    "error": "Coordenadas inválidas. Por favor, permita o acesso à sua localização.",
                    "show_distance": True,
                },
            )

        # Store coordinates in session for subsequent GET requests (filters)
        request.session["user_lat"] = user_lat
        request.session["user_lon"] = user_lon
    else:
        # GET request - retrieve from session
        try:
            user_lat = float(request.session.get("user_lat"))
            user_lon = float(request.session.get("user_lon"))
        except (TypeError, ValueError):
            return render(
                request,
                "parishes_by_city.html",
                {
                    "error": "Coordenadas inválidas. Por favor, permita o acesso à sua localização.",
                    "show_distance": True,
                },
            )

    day_name = request.GET.get("dia")
    hour = request.GET.get("horario")
    type_name = request.GET.get("tipo")
    verified_only = request.GET.get("verificado") == "1"
    max_distance = request.GET.get("distancia", "50")

    try:
        max_distance = float(max_distance)
    except ValueError:
        max_distance = 50.0

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

    schedules = Schedule.objects.filter(
        location__isnull=False,
        type=type,
    )

    if day is not None:
        schedules = schedules.filter(day=day)

    if hour is not None:
        hour = time(int(hour))
        qs = Q(start_time__gte=hour) | Q(end_time__gte=hour)
        schedules = schedules.filter(qs)

    if verified_only:
        schedules = schedules.filter(verified_at__isnull=False)

    schedules = schedules.select_related(
        "parish", "parish__city", "parish__city__state", "source", "location"
    ).prefetch_related("parish__contact")

    schedules_with_distance = []
    for schedule in schedules:
        distance = haversine_distance(
            user_lat,
            user_lon,
            float(schedule.location.latitude),
            float(schedule.location.longitude),
        )
        if distance <= max_distance:
            schedule.distance = distance
            schedules_with_distance.append(schedule)

    schedules_with_distance.sort(key=lambda s: s.distance)

    template = (
        "cards.html"
        if request.htmx and not request.htmx.boosted
        else "parishes_by_city.html"
    )

    return render(
        request,
        template,
        {
            "schedules": schedules_with_distance,
            "day": day,
            "hour": hour.hour if hour else 0,
            "type": type,
            "max_distance": max_distance,
            "show_distance": True,
            "Schedule": Schedule,
        },
    )


@csrf_exempt
def create_contact(request):
    # TODO: tests
    # TODO: handle backend errors in the ui; show a message
    # TODO: "add another" button
    # TODO: modal to component
    # TODO: form to component

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    ddd = request.POST.get("ddd")
    number = request.POST.get("number")
    whatsapp = f"+55{ddd}{number}"

    contact_request = ContactRequest(whatsapp=whatsapp)
    contact_request.full_clean()
    contact_request.save()

    if request.htmx:
        template = """
        <div id="successMessage">
            <div class="alert alert-success" role="alert">
                <i class="fa-solid fa-check-circle me-2"></i>
                Obrigado! Em breve entraremos em contato com a paróquia.
            </div>
        </div>
        """
        return HttpResponse(template)

    return redirect(request.META.get("HTTP_REFERER", "/"))
