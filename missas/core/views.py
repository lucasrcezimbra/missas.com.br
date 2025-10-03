from datetime import datetime, time, timedelta, timezone

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


def _get_brazilian_now():
    brazilian_tz = timezone(timedelta(hours=-3))
    utc_now = datetime.now(timezone.utc)
    return utc_now.astimezone(brazilian_tz)


# @vary_on_headers("HX-Request")  # TODO: Cloudflare ignores Vary header
def by_city(request, state, city):
    city = get_object_or_404(City, slug=city, state__slug=state)

    now_brazilian = _get_brazilian_now()

    day_to_name = {
        0: "segunda",
        1: "terca",
        2: "quarta",
        3: "quinta",
        4: "sexta",
        5: "sabado",
        6: "domingo",
    }

    day_name = request.GET.get("dia")
    hour_param = request.GET.get("horario")
    type_name = request.GET.get("tipo")
    verified_only = request.GET.get("verificado") == "1"

    has_missing_params = day_name is None or hour_param is None or type_name is None

    if day_name is None:
        day_name = day_to_name[now_brazilian.weekday()]

    if hour_param is None:
        hour_param = str(now_brazilian.hour)

    if type_name is None:
        type_name = "missas"

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

    if hour_param is not None:
        hour = time(int(hour_param))
        qs = Q(start_time__gte=hour) | Q(end_time__gte=hour)
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
            "hour": int(hour_param) if hour_param else 0,
            "type": type,
            "Schedule": Schedule,
        },
    )

    if has_missing_params:
        from django.http import QueryDict

        query = QueryDict(mutable=True)
        query["tipo"] = type_name
        query["dia"] = day_name
        query["horario"] = hour_param
        if verified_only:
            query["verificado"] = "1"
        response["HX-Replace-Url"] = f"{request.path}?{query.urlencode()}"

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
