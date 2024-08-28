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
    return render(
        request,
        "cities_by_state.html",
        context={"state": state, "cities": state.cities.all()},
    )


# @vary_on_headers("HX-Request")  # TODO: Cloudflare ignores Vary header
def by_city(request, state, city):
    city = get_object_or_404(City, slug=city, state__slug=state)
    day_name = request.GET.get("dia")
    hour = request.GET.get("horario")
    type_name = request.GET.get("tipo")
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

    schedules = schedules.order_by("day", "start_time")

    template = "index.html"

    if request.htmx:
        template = "cards.html"

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


# SCHEDULES = [
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora da Candelária - Candelária"},
#     #     "day": EVERY 2ND,
#     #     "time": time(12, 00),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Sant'Ana - Capim Macio"},
#     #     "day": "TODO DIA 26",
#     #     "time": time(19, 00),
#     # },
#     # {
#     #     "church": {"name": "Paróquia do Sagrado Coração de Jesus - Morro Branco"},
#     #     "day": 1ST FRIDAY OF THE MONTH,
#     #     "time": time(17, 00),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora Rainha da Paz - Nova Parnamirim"},
#     #     "day": FIRST FRIDAY,
#     #     "time": time(17, 00),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora de Fátima - Ribeira"},
#     #     "day": EVERY 13TH,
#     #     "time": time(12, 00),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora do Carmo - Pq. das Nações"},
#     #     "day": DAY 16,
#     #     "time": time(19, 30),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora do Perpétuo Socorro - Quintas"},
#     #     "day": FIRST FRIDAY OF THE MONTH,
#     #     "time": time(18, 0),
#     # },
#     #     {
#     #         "church": {"name": "Paróquia do Santuário dos Santos Mártires - Nazaré"},
#     #         "day": FIRST FRIDAY OF THE MONTH,
#     #         "time": time(19, 0),
#     #     },
#     #     {
#     #         "church": {"name": "Paróquia do Santuário dos Santos Mártires - Nazaré"},
#     #         "day": EVERY DAY 3RD,
#     #     "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia da Imaculada Conceição - Nova Aliança"},
#     #     "day": DECEMBER 8TH,
#     #     "time": time(19, 0),
#     # },
#     #     {
#     #         "church": {"name": "Paróquia de São João Batista - Praia de Pitangui"},
#     #         "day": FIRST FRIDAY,
#     #     "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de São João Batista - Praia de Pitangui"},
#     #     "day": LAST WEDNESDAY,
#     # "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de São Tiago Menor - Santarém"},
#     #     "day": 1ST FRIDAY,
#     #     "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de São Tiago Menor - Santarém"},
#     #     "day": 3RD DAY OF EVERY MONTH,
#     # "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora da Conceição - Macaíba"},
#     #     "day": FIRST FRIDAY OF THE MONTH,
#     #     "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de São Gonçalo - São Gonçalo do Amarante"},
#     #     "day": FIRST FRIDAY,
#     # "time": time(19, 30),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora dos Impossíveis - Pitimbu"},
#     #     "day": LAST WEDNESDAY OF THE MONTH,
#     #     "time": time(19, 0),
#     # },
#     #     {
#     #         "church": {"name": "Paróquia do Bom Jesus das Dores - Ribeira"},
#     #         "day": 1ST SATURDAY OF THE MONTH,
#     #     "time": time(8, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Santo André de Soveral - Emaús"},
#     #     "day": DAY 3,
#     # "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Santo André de Soveral - Emaús"},
#     #     "day": DAY 29,
#     # "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Santo André de Soveral - Emaús"},
#     #     "day": 1ST FRIDAY,
#     #     "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora das Graças - Afonso Bezerra"},
#     #     "day": FIRST FRIDAY,
#     # "time": time(19, 0),
#     # },
#     #     {
#     #         "church": {"name": "Paróquia de Nossa Senhora Mãe dos Homens - João Câmara"},
#     #         "day": 1ST FRIDAY OF THE MONTH,
#     #     "time": time(7, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora Mãe dos Homens - João Câmara"},
#     #     "day": 3RD THURSDAY OF THE MONTH,
#     # "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Área Pastoral de Nossa Senhora das Dores - Ceará-Mirim"},
#     #     "day": 1ST FRIDAY OF THE MONTH,
#     # "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Área Pastoral de Nossa Senhora das Dores - Ceará-Mirim"},
#     #     "day": 15TH OF EVERY MONTH,
#     #     "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Área Pastoral de Nossa Senhora do Rosário de Fátima - Ceará-Mirim"},
#     #     "day": 04,
#     #     "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Área Pastoral de Nossa Senhora do Rosário de Fátima - Ceará-Mirim"},
#     #     "day": 13,
#     #     "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Área Pastoral de Nossa Senhora do Rosário de Fátima - Ceará-Mirim"},
#     #     "day": 22,
#     #     "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Área Pastoral de Nossa Senhora do Rosário de Fátima - Ceará-Mirim"},
#     #     "day": 1ST THURSDAY,
#     #     "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora do Livramento - Taipu"},
#     #     "day": FIRST FRIDAY,
#     # "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora do Livramento - Taipu"},
#     #     "day": LAST MONDAY,
#     # "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora do Amparo - Coronel Ezequiel"},
#     #     "day": FIRST FRIDAY,
#     # "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora do Amparo - Coronel Ezequiel"},
#     #     "day": EVERY 29TH DAY,
#     # "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de São José - São José de Campestre"},
#     #     "day": FIRST FRIDAY,
#     # "time": time(17, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de São José - São José de Campestre"},
#     #     "day": 19TH OF EACH MONTH,
#     #     "time": time(19, 0),
#     # },
#     # {
#     #     "church": {"name": "Paróquia de Nossa Senhora dos Prazeres - Goianinha"},
#     #     "day": FIRST FRIDAY OF EVERY MONTH,
#     #     "time": time(19, 30),
#     # },
# ]
