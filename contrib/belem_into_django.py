import json
import os
from datetime import datetime
from textwrap import dedent

import django
import llm
from decouple import config
from django.db.utils import IntegrityError
from django.utils.dateparse import parse_time
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Parish, Schedule, Source, State  # noqa

OPENAI_API_KEY = config("OPENAI_API_KEY")

with open("./contrib/belem.jsonl") as f:
    datas = [json.loads(line) for line in f.readlines()]

if not datas:
    print("No data found in belem.jsonl")
    exit(0)

state, _ = State.objects.get_or_create(
    short_name="PA",
    defaults={"name": "Pará", "slug": "para"},
)

city, _ = City.objects.get_or_create(
    name="Belém",
    state=state,
    defaults={"slug": "belem"},
)

source, _ = Source.objects.get_or_create(
    type=Source.Type.SITE,
    description="Arquidiocese de Belém",
    defaults={"link": "https://arquidiocesedebelem.com.br/"},
)

model = llm.get_model("gpt-4o")
model.key = OPENAI_API_KEY


def ynput():
    while True:
        yn = input("Approve? (Y/n) ")
        if yn == "Y":
            return True
        elif yn == "n":
            return False


for data in datas:
    parish_name = data["parish_name"].strip()
    times = data.get("times", [])

    if not times:
        print(f"No times found for {parish_name}, skipping")
        continue

    times_text = "\n".join(times)

    parish, created = Parish.objects.get_or_create(
        city=city,
        name=parish_name,
        defaults={"slug": slugify(parish_name)},
    )

    if created:
        print(f"Created parish: {parish}")

    ai_response = model.prompt(
        times_text,
        system=dedent(
            """\
            You are a Django management tool. You help to create new objects based on scraped schedule text.
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

            An example input:
            ```
            Segunda a sexta-feira - 11h e 16h30 Sábado - 11h e 16h30
            Domingo - 7h, 11h e 19h
            ```

            Example output:
            ```json
            {
                "schedules": [
                    {
                        "day": 1,
                        "location_name": "",
                        "observation": "",
                        "start_time": "11:00",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 1,
                        "location_name": "",
                        "observation": "",
                        "start_time": "16:30",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 2,
                        "location_name": "",
                        "observation": "",
                        "start_time": "11:00",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 2,
                        "location_name": "",
                        "observation": "",
                        "start_time": "16:30",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 3,
                        "location_name": "",
                        "observation": "",
                        "start_time": "11:00",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 3,
                        "location_name": "",
                        "observation": "",
                        "start_time": "16:30",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 4,
                        "location_name": "",
                        "observation": "",
                        "start_time": "11:00",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 4,
                        "location_name": "",
                        "observation": "",
                        "start_time": "16:30",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 5,
                        "location_name": "",
                        "observation": "",
                        "start_time": "11:00",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 5,
                        "location_name": "",
                        "observation": "",
                        "start_time": "16:30",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 6,
                        "location_name": "",
                        "observation": "",
                        "start_time": "11:00",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 6,
                        "location_name": "",
                        "observation": "",
                        "start_time": "16:30",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 0,
                        "location_name": "",
                        "observation": "",
                        "start_time": "07:00",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 0,
                        "location_name": "",
                        "observation": "",
                        "start_time": "11:00",
                        "end_time": null,
                        "type": "mass"
                    },
                    {
                        "day": 0,
                        "location_name": "",
                        "observation": "",
                        "start_time": "19:00",
                        "end_time": null,
                        "type": "mass"
                    }
                ]
            }
            ```

            Instructions:
            - Parse the Portuguese text to extract schedule information
            - Create separate schedule entries for each day and time combination
            - Use 24-hour format for times (e.g., "07:00", "19:00")
            - Default to "mass" type unless explicitly stated as confession/confissão
            - Leave verified_at as null
            - Extract location_name if mentioned in the text
            - Put any special notes in the observation field
            """
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
                parish=parish,
                day=s["day"],
                type=s.get("type", "mass"),
                start_time=start_time,
            )
        except Schedule.DoesNotExist:
            schedule = Schedule(
                parish=parish,
                day=s["day"],
                type=s.get("type", "mass"),
                start_time=start_time,
            )

        schedule.end_time = end_time
        schedule.location_name = s.get("location_name", "")
        schedule.observation = s.get("observation", "")
        schedule.source = source

        schedules.append(schedule)

    existing_schedules = Schedule.objects.filter(parish=parish)
    to_be_deleted = [s for s in existing_schedules if s not in schedules]

    print("=" * 150)
    print(f"Parish: {parish}")
    print(f"Times text:\n{times_text}")
    print("=" * 150)

    for s in to_be_deleted:
        print(
            "DELETE?",
            s.type,
            s,
            s.observation or "",
            s.tracker.changed() if hasattr(s, "tracker") else "",
        )

        if ynput():
            s.delete()

        print("-" * 100)

    print("=" * 150)

    for s in schedules:
        if s.pk and not s.tracker.changed():
            print("Didn't change", s.type, s, s.observation or "")
            print("-" * 100)
            continue

        if s.pk:
            message = "UPDATE?"
        else:
            message = "CREATE?"

        print(
            message,
            s.type,
            s,
            s.observation or "",
            s.tracker.changed() if hasattr(s, "tracker") and s.pk else "NEW",
        )

        if ynput():
            s.save()

        print("-" * 100)

    print("=" * 150)
    print()
