from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.db import models
from django.db.models import Q
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from missas.core.models import City, ContactRequest, Parish, Schedule, State

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")

DAY_SLUG_TO_ENUM = {
    "domingo": Schedule.Day.SUNDAY,
    "segunda": Schedule.Day.MONDAY,
    "terca": Schedule.Day.TUESDAY,
    "quarta": Schedule.Day.WEDNESDAY,
    "quinta": Schedule.Day.THURSDAY,
    "sexta": Schedule.Day.FRIDAY,
    "sabado": Schedule.Day.SATURDAY,
}

WEEKDAY_TO_DAY_SLUG = {
    0: "segunda",
    1: "terca",
    2: "quarta",
    3: "quinta",
    4: "sexta",
    5: "sabado",
    6: "domingo",
}

TYPE_SLUG_TO_CHOICE = {
    "missas": Schedule.Type.MASS,
    "confissoes": Schedule.Type.CONFESSION,
}

DEFAULT_TYPE_SLUG = "missas"


def get_brazil_now():
    return datetime.now(BRAZIL_TZ)


def _parse_hour(value):
    if value is None:
        return None

    try:
        hour_value = int(value)
    except (TypeError, ValueError):
        return None

    if 0 <= hour_value <= 23:
        return hour_value

    return None


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
    query_params = request.GET.copy()
    query_params._mutable = True
    verified_only = query_params.get("verificado") == "1"

    now = get_brazil_now()
    default_day_slug = WEEKDAY_TO_DAY_SLUG[now.weekday()]
    default_hour = now.hour

    type_slug = query_params.get("tipo")
    type_choice = TYPE_SLUG_TO_CHOICE.get(type_slug)

    should_push_url = False

    if type_choice is None:
        type_slug = DEFAULT_TYPE_SLUG
        type_choice = TYPE_SLUG_TO_CHOICE[type_slug]
        query_params["tipo"] = type_slug
        should_push_url = True

    day_slug = query_params.get("dia")
    day = DAY_SLUG_TO_ENUM.get(day_slug)

    if type_choice == Schedule.Type.MASS and day is None:
        day_slug = default_day_slug
        day = DAY_SLUG_TO_ENUM[day_slug]
        query_params["dia"] = day_slug
        should_push_url = True

    hour_value = _parse_hour(query_params.get("horario"))

    if type_choice == Schedule.Type.MASS and hour_value is None:
        hour_value = default_hour
        query_params["horario"] = str(hour_value)
        should_push_url = True

    hour_filter = time(hour_value) if hour_value is not None else None

    schedules = Schedule.objects.filter(parish__city=city, type=type_choice)

    if day is not None:
        schedules = schedules.filter(day=day)

    if hour_filter is not None:
        qs = Q(start_time__gte=hour_filter) | Q(end_time__gte=hour_filter)
        schedules = schedules.filter(qs)

    if verified_only:
        schedules = schedules.filter(verified_at__isnull=False)

    schedules = schedules.order_by("day", "start_time")
    schedules = schedules.select_related(
        "parish", "parish__city", "parish__city__state", "source"
    ).prefetch_related("parish__contact")
    template = (
        "cards.html"
        if request.htmx and not request.htmx.boosted
        else "parishes_by_city.html"
    )

    response = render(
        request,
        template,
        {
            "schedules": schedules,
            "day": day,
            "city": city,
            "hour": hour_value if hour_value is not None else 0,
            "type": type_choice,
            "Schedule": Schedule,
        },
    )

    if should_push_url:
        query_string = query_params.urlencode()
        canonical_url = request.path

        if query_string:
            canonical_url = f"{canonical_url}?{query_string}"

        response["HX-Push-Url"] = canonical_url

    return response


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
