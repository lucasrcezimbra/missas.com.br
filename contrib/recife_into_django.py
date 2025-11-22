import json
import os
from textwrap import dedent

import django
import llm
from decouple import config
from django.utils.dateparse import parse_time
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Parish, Schedule, Source, State  # noqa

OPENAI_API_KEY = config("OPENAI_API_KEY")

with open("./contrib/recife.jsonl") as f:
    datas = [json.loads(line) for line in f.readlines()]

state, _ = State.objects.get_or_create(
    short_name="PE",
    defaults={"name": "Pernambuco", "slug": "pernambuco"},
)

source, _ = Source.objects.get_or_create(
    type=Source.Type.SITE,
    description="Site da Arquidiocese de Olinda e Recife",
    defaults={"link": "https://www.arquidioceseolindarecife.org/horarios-de-missas/"},
)

print(f"State: {state}")
print(f"Source: {source}")
print(f"Total parishes to import: {len(datas)}")
print("=" * 100)

model = llm.get_model("gpt-4o")
model.key = OPENAI_API_KEY

for idx, data in enumerate(datas, 1):
    parish_name = data["parish_name"]
    location = data.get("location", "")
    times = data.get("times", [])

    if not location:
        print(f"[{idx}/{len(datas)}] SKIP: {parish_name} - No location")
        continue

    city_name = location.split("/")[-1].strip()

    try:
        city = City.objects.get(name=city_name, state=state)
    except City.DoesNotExist:
        city = City.objects.create(
            name=city_name, state=state, slug=slugify(city_name)
        )
        print(f"Created city: {city}")

    parish, created = Parish.objects.get_or_create(
        city=city,
        name=parish_name,
        defaults={"slug": slugify(parish_name)},
    )

    if created:
        print(f"[{idx}/{len(datas)}] Created parish: {parish}")
    else:
        print(f"[{idx}/{len(datas)}] Found parish: {parish}")

    times_text = "\n".join(times)

    ai_response = model.prompt(
        times_text,
        system=dedent(
            """\
            You are a Django management tool. You help to create Schedule objects from Mass schedule text.
            This is the Django model:

            ```python
            class Schedule(models.Model):
                class Day(models.IntegerChoices):
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

                day = models.IntegerField(choices=Day.choices)
                location_name = models.CharField(max_length=128, blank=True)
                observation = models.TextField(blank=True)
                start_time = models.TimeField()
                end_time = models.TimeField(null=True, blank=True)
                type = models.CharField(choices=Type.choices, default=Type.MASS)
            ```

            Your output will be used to create multiple Schedules.
            Parse the Mass schedule text and extract all schedules.
            Return a JSON object with a "schedules" array.
            Each schedule should have: day (0-6), start_time (HH:MM format), type (mass or confession), location_name (if mentioned), observation (if any special notes).
            Ignore phone numbers and other non-schedule information.

            Example input:
            ```
            Terças-feiras: 11h
            Quintas-feiras: 16h
            Sextas-feiras: 6h; 8h; 10h; 12h; 15h e 17h
            Domingos: 8h
            Telefone: 3424.8500
            ```

            Example output:
            ```json
            {
                "schedules": [
                    {"day": 2, "start_time": "11:00", "type": "mass", "location_name": "", "observation": ""},
                    {"day": 4, "start_time": "16:00", "type": "mass", "location_name": "", "observation": ""},
                    {"day": 5, "start_time": "06:00", "type": "mass", "location_name": "", "observation": ""},
                    {"day": 5, "start_time": "08:00", "type": "mass", "location_name": "", "observation": ""},
                    {"day": 5, "start_time": "10:00", "type": "mass", "location_name": "", "observation": ""},
                    {"day": 5, "start_time": "12:00", "type": "mass", "location_name": "", "observation": ""},
                    {"day": 5, "start_time": "15:00", "type": "mass", "location_name": "", "observation": ""},
                    {"day": 5, "start_time": "17:00", "type": "mass", "location_name": "", "observation": ""},
                    {"day": 0, "start_time": "08:00", "type": "mass", "location_name": "", "observation": ""}
                ]
            }
            ```

            Notes:
            - Sunday=0, Monday=1, Tuesday=2, Wednesday=3, Thursday=4, Friday=5, Saturday=6
            - Convert times to HH:MM format (e.g., "19h" -> "19:00", "6h30" -> "06:30")
            - Handle ranges like "Segunda a sábado" (Monday to Saturday) by creating individual schedules for each day
            - If confession times are mentioned, use type "confession", otherwise use "mass"
            - Ignore "Telefone:" lines and other non-schedule information
            """
        ),
        json_object=True,
    )

    try:
        schedule_data = json.loads(ai_response.text())
        schedules_to_create = []

        for s in schedule_data.get("schedules", []):
            start_time = parse_time(s["start_time"])
            end_time = parse_time(s["end_time"]) if s.get("end_time") else None

            schedule, created = Schedule.objects.get_or_create(
                parish=parish,
                day=s["day"],
                start_time=start_time,
                defaults={
                    "type": s.get("type", "mass"),
                    "location_name": s.get("location_name", ""),
                    "observation": s.get("observation", ""),
                    "end_time": end_time,
                    "source": source,
                },
            )

            if created:
                schedules_to_create.append(schedule)

        if schedules_to_create:
            print(f"  Created {len(schedules_to_create)} schedules")

    except Exception as e:
        print(f"  ERROR parsing schedules: {e}")
        print(f"  Times text: {times_text}")
        continue

    print("-" * 100)

print("=" * 100)
print("Import completed!")
