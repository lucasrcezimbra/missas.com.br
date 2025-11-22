import json
import os
from datetime import datetime
from textwrap import dedent

import django
import llm
from decouple import config
from django.utils.dateparse import parse_time
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Parish, Schedule, Source, State  # noqa


def ynput():
    while True:
        yn = input("Approve? (Y/n) ")
        if yn == "Y":
            return True
        elif yn == "n":
            return False


with open("./contrib/palmas.jsonl") as f:
    datas = [json.loads(line) for line in f.readlines()]

state, _ = State.objects.get_or_create(
    short_name="TO",
    defaults={"name": "Tocantins", "slug": "tocantins"},
)
print(f"{state=}")

city, _ = City.objects.get_or_create(
    name="Palmas",
    state=state,
    defaults={"slug": "palmas"},
)
print(f"{city=}")

source, _ = Source.objects.get_or_create(
    type=Source.Type.SITE,
    description="Arquidiocese de Palmas",
    defaults={"link": "https://arquidiocesedepalmas.org.br/horarios-de-missas/"},
)
print(f"{source=}")

model = llm.get_model("o3-mini")
model.key = config("OPENAI_API_KEY")

today = datetime.now().date().isoformat()

for data in datas:
    parish_name = data["parish_name"]
    times = data["times"]

    parish, created = Parish.objects.get_or_create(
        city=city,
        name=parish_name,
        defaults={"slug": slugify(parish_name)},
    )

    if created:
        print(f"Created: {parish}")
    else:
        print(f"Found: {parish}")

    times_text = "\n".join(times)

    ai_response = model.prompt(
        times_text,
        system=dedent(
            f"""\
            You are a Django management tool. You help to create new objects based on scraped mass schedule data.
            This is the Django model:

            ```python
            class Schedule(models.Model):
                class Day(models.IntegerChoices):
                    # It's integer to make the ordering easier
                    SUNDAY = (0, "Domingo")
                    MONDAY = (1, "Segunda-feira")
                    TUESDAY = (2, "Terça-feira")
                    WEDNESDAY = (3, "Quarta-feira")
                    THURSDAY = (4, "Quinta-feira")
                    FRIDAY = (5, "Sexta-feira")
                    SATURDAY = (6, "Sábado")

                class Type(models.TextChoices):
                    MASS = ("mass", "Missa")
                    CONFESSION = ("confession", "Confissão")

                created_at = models.DateTimeField(auto_now_add=True)
                updated_at = models.DateTimeField(auto_now=True)
                day = models.IntegerField(choices=Day.choices)
                location_name = models.CharField(max_length=128, blank=True)
                observation = models.TextField(null=True, blank=True)
                parish = models.ForeignKey(
                    Parish, on_delete=models.CASCADE, related_name="schedules"
                )
                source = models.ForeignKey(Source, on_delete=models.RESTRICT, blank=True, null=True)
                start_time = models.TimeField()
                end_time = models.TimeField(null=True, blank=True)
                type = models.CharField(choices=Type.choices, default=Type.MASS)
                verified_at = models.DateField(blank=True, null=True)

                class Meta:
                    unique_together = ("parish", "day", "start_time")
            ```

            Your output will be used to create multiple Schedules.
            ```python
            for schedule_data in json.loads(ai_response)['schedules']:
                schedules = Schedule(parish=parish, source=source, **schedule_data)

            Schedule.objects.delete(parish=parish)
            Schedule.objects.bulk_create(schedules)
            ```

            Parse the input text and extract all mass schedules.
            - Convert day names to integers (Domingo=0, Segunda=1, Terça=2, Quarta=3, Quinta=4, Sexta=5, Sábado=6)
            - Extract start times in HH:MM format
            - If a location/community name is mentioned (e.g., "Matriz", "Comunidade Santa Luzia"), put it in location_name
            - If there are special notes (e.g., "missa e adoração", "uma vez ao mês"), put them in observation
            - Set type to "mass" for missas, "confession" for confissões
            - Set verified_at to "{today}"
            - For time ranges like "Segunda a sexta" create separate entries for each day
            - For times like "19h" convert to "19:00"
            - For times like "19h30" convert to "19:30"

            An example:
            Input:
            ```
            Matriz
            Segunda: 19h30 (missa e adoração)
            Sexta: 19h30
            Sábado: 8h
            Domingo: 8h, 10h e 19h30
            Comunidade Santa Luzia
            Domingo: 8h e 18h
            Terça: 19h30
            ```

            AI response:
            ```json
            {{
                "schedules": [
                    {{
                        "day": 1,
                        "location_name": "Matriz",
                        "observation": "Missa e adoração",
                        "start_time": "19:30",
                        "end_time": null,
                        "type": "mass",
                        "verified_at": "{today}"
                    }},
                    {{
                        "day": 5,
                        "location_name": "Matriz",
                        "observation": "",
                        "start_time": "19:30",
                        "end_time": null,
                        "type": "mass",
                        "verified_at": "{today}"
                    }},
                    {{
                        "day": 6,
                        "location_name": "Matriz",
                        "observation": "",
                        "start_time": "08:00",
                        "end_time": null,
                        "type": "mass",
                        "verified_at": "{today}"
                    }},
                    {{
                        "day": 0,
                        "location_name": "Matriz",
                        "observation": "",
                        "start_time": "08:00",
                        "end_time": null,
                        "type": "mass",
                        "verified_at": "{today}"
                    }},
                    {{
                        "day": 0,
                        "location_name": "Matriz",
                        "observation": "",
                        "start_time": "10:00",
                        "end_time": null,
                        "type": "mass",
                        "verified_at": "{today}"
                    }},
                    {{
                        "day": 0,
                        "location_name": "Matriz",
                        "observation": "",
                        "start_time": "19:30",
                        "end_time": null,
                        "type": "mass",
                        "verified_at": "{today}"
                    }},
                    {{
                        "day": 0,
                        "location_name": "Comunidade Santa Luzia",
                        "observation": "",
                        "start_time": "08:00",
                        "end_time": null,
                        "type": "mass",
                        "verified_at": "{today}"
                    }},
                    {{
                        "day": 0,
                        "location_name": "Comunidade Santa Luzia",
                        "observation": "",
                        "start_time": "18:00",
                        "end_time": null,
                        "type": "mass",
                        "verified_at": "{today}"
                    }},
                    {{
                        "day": 2,
                        "location_name": "Comunidade Santa Luzia",
                        "observation": "",
                        "start_time": "19:30",
                        "end_time": null,
                        "type": "mass",
                        "verified_at": "{today}"
                    }}
                ]
            }}
            ```"""
        ),
        json_object=True,
    )

    schedule_data = json.loads(ai_response.text())

    schedules = []

    for s in schedule_data["schedules"]:
        start_time = parse_time(s.pop("start_time"))

        if end_time := s.pop("end_time", None):
            end_time = parse_time(end_time)

        try:
            schedule = Schedule.objects.get(
                parish=parish, day=s["day"], type=s["type"], start_time=start_time
            )
        except Schedule.DoesNotExist:
            schedule = Schedule(
                parish=parish, day=s["day"], type=s["type"], start_time=start_time
            )

        schedule.end_time = end_time

        if s["location_name"].lower() != schedule.location_name.lower():
            schedule.location_name = s["location_name"]

        if s["observation"].lower() != schedule.observation.lower():
            schedule.observation = s["observation"]

        schedule.source = source
        schedule.verified_at = datetime.strptime(s["verified_at"], "%Y-%m-%d").date()

        schedules.append(schedule)

    to_be_deleted = [
        s for s in Schedule.objects.filter(parish=parish) if s not in schedules
    ]

    print("=" * 150)

    print(f"Parish: {parish}")
    print(f"Input:\n{times_text}")

    print("=" * 150)

    for s in to_be_deleted:
        print("DELETE?", s.type, s, s.observation or "", s.tracker.changed())

        if ynput():
            s.delete()

        print("-" * 100)

    print("=" * 150)

    for s in schedules:
        if not s.tracker.changed():
            print("Didn't change", s.type, s, s.observation or "", s.tracker.changed())
            print("-" * 100)
            continue

        if s.pk:
            message = "UPDATE?"
        else:
            message = "CREATE?"

        print(message, s.type, s, s.observation or "", s.tracker.changed())

        if ynput():
            s.save()

        print("-" * 100)

    print("=" * 150)
