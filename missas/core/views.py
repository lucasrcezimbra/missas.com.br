from datetime import time

from django.db.models import Q
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from missas.core.models import City, ContactRequest, Schedule, State


def index(request):
    states = State.objects.prefetch_related("cities").all().order_by("name")

    # Create a list to hold states with their cities
    states_with_cities = []
    for state in states:
        # Get cities with schedules for this state
        cities = (
            state.cities.annotate_has_schedules()
            .order_by("-has_schedules", "name")
            .all()
        )
        if cities:
            # Create a dict with state info and its cities
            state_data = {
                "state": state,
                "cities": cities,
            }
            states_with_cities.append(state_data)

    return render(request, "home.html", {"states": states_with_cities})


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
    schedules = schedules.prefetch_related("parish", "parish__contact", "source")
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
