import json
import os
import sys
from datetime import datetime
from textwrap import dedent

import django
import llm
from decouple import config
from django.utils.dateparse import parse_time
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Parish, Schedule, Source  # noqa


if len(sys.argv) < 2:
    print("Usage: poetry run python contrib/teresina_import.py <jsonl_file>")
    sys.exit(1)

jsonl_file = sys.argv[1]

with open(jsonl_file) as f:
    datas = [json.loads(line) for line in f.readlines()]

city = City.objects.get(name="Teresina", state__short_name="PI")
print(f"{city=}")

source, _ = Source.objects.get_or_create(
    type=Source.Type.SITE,
    description="Site da Arquidiocese de Teresina",
    link="https://arquidiocesedeteresina.org.br/",
)
print(f"{source=}")

model = llm.get_model("gpt-4o-mini")
model.key = config("OPENAI_API_KEY")


def ynput():
    while True:
        yn = input("Approve? (Y/n) ")
        if yn == "Y":
            return True
        elif yn == "n":
            return False


for data in datas:
    parish_name = data["parish_name"]
    times_text = "\n".join(data["times"])

    if not parish_name or not times_text.strip():
        print(f"Skipping entry with missing data: {parish_name=}")
        continue

    print("=" * 150)
    print(f"Processing: {parish_name}")
    print(f"Times:\n{times_text}")
    print("=" * 150)

    parish, created = Parish.objects.get_or_create(
        city=city,
        slug=slugify(parish_name),
        defaults={"name": parish_name},
    )

    if created:
        print(f"Created new parish: {parish}")

    ai_response = model.prompt(
        times_text,
        system=dedent(
            """\
            You are a Django management tool. You help to create Schedule objects from scraped parish schedule text.
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

            Schedule.objects.bulk_create(schedules)
            ```

            Parse the schedule text and extract all mass and confession times.
            Return a JSON object with a "schedules" array containing objects with these fields:
            - day: integer (0=Sunday, 1=Monday, etc)
            - start_time: string in HH:MM format
            - end_time: string in HH:MM format or null
            - type: "mass" or "confession"
            - location_name: string (if location is mentioned, otherwise empty)
            - observation: string (any special notes, otherwise empty)
            - verified_at: current date in YYYY-MM-DD format

            Example response:
            ```json
            {
                "schedules": [
                    {
                        "day": 0,
                        "start_time": "09:00",
                        "end_time": null,
                        "type": "mass",
                        "location_name": "",
                        "observation": "",
                        "verified_at": "2024-11-22"
                    }
                ]
            }
            ```"""
        ),
        json_object=True,
    )

    try:
        parsed_data = json.loads(ai_response.text())
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response: {e}")
        print(f"Response: {ai_response.text()}")
        continue

    schedules = []

    for s in parsed_data["schedules"]:
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
