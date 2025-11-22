import json
import os
import re
from datetime import time

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Parish, Schedule, Source  # noqa

DAY_MAPPING = {
    "DOM": Schedule.Day.SUNDAY,
    "SEG": Schedule.Day.MONDAY,
    "TER": Schedule.Day.TUESDAY,
    "QUA": Schedule.Day.WEDNESDAY,
    "QUI": Schedule.Day.THURSDAY,
    "SEX": Schedule.Day.FRIDAY,
    "SAB": Schedule.Day.SATURDAY,
}

TYPE_MAPPING = {
    "Missas": Schedule.Type.MASS,
    "Confissão": Schedule.Type.CONFESSION,
    "Confissões": Schedule.Type.CONFESSION,
}


def parse_time(time_str):
    """Parse time string like '08h', '19h30', '7h', etc."""
    time_str = time_str.strip().lower()
    if not time_str:
        return None

    match = re.match(r"(\d{1,2})h(\d{2})?", time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        return time(hour=hour, minute=minute)
    return None


def extract_city_name(location_text):
    """Extract city name from location text like 'BAIRRO ATALAIA, ARACAJU-SE'"""
    parts = location_text.split(",")
    if len(parts) >= 2:
        city_part = parts[-1].strip()
        city_name = city_part.split("-")[0].strip()
        return city_name
    elif "-SE" in location_text:
        city_name = location_text.split("-")[0].strip()
        return city_name
    return "Aracaju"


with open("./contrib/aracaju.jsonl") as f:
    datas = [json.loads(line) for line in f.readlines()]

source, _ = Source.objects.get_or_create(
    link="https://arquidiocesedearacaju.org/horarios-de-missa/",
    defaults={
        "description": "Site da Arquidiocese de Aracaju",
        "type": Source.Type.SITE,
    },
)

print(f"Processing {len(datas)} parishes...")

for d in datas:
    parish_full_name = d["parish_name"].strip()

    if "–" in parish_full_name:
        parts = parish_full_name.split("–", 1)
        parish_name = parts[0].strip()
        location_text = parts[1].strip() if len(parts) > 1 else ""
    elif "-" in parish_full_name and "," in parish_full_name:
        parts = parish_full_name.split("-", 1)
        parish_name = parts[0].strip()
        location_text = parts[1].strip() if len(parts) > 1 else ""
    else:
        parish_name = parish_full_name
        location_text = ""

    city_name = extract_city_name(location_text) if location_text else "Aracaju"

    try:
        city = City.objects.get(name=city_name, state__short_name="SE")
    except City.DoesNotExist:
        try:
            city = City.objects.get(name__icontains=city_name, state__short_name="SE")
        except (City.DoesNotExist, City.MultipleObjectsReturned):
            city = City.objects.get(name="Aracaju", state__short_name="SE")

    parish, created = Parish.objects.get_or_create(
        city=city, slug=slugify(parish_name), defaults={"name": parish_name}
    )

    if created:
        print(f"✓ Created parish: {parish}")

    schedules_created = 0
    for time_entry in d.get("times", []):
        parts = [p.strip() for p in time_entry.split("|")]
        if len(parts) < 3:
            continue

        schedule_type_str = parts[0]
        day_str = parts[1]
        time_parts = parts[2:]

        schedule_type = TYPE_MAPPING.get(schedule_type_str, Schedule.Type.MASS)
        day = DAY_MAPPING.get(day_str)

        if day is None:
            continue

        for time_part in time_parts:
            if not time_part:
                continue

            start_time = parse_time(time_part)
            if start_time is None:
                continue

            try:
                schedule, created = Schedule.objects.get_or_create(
                    parish=parish,
                    day=day,
                    start_time=start_time,
                    defaults={
                        "type": schedule_type,
                        "observation": "",
                        "source": source,
                    },
                )
                if created:
                    schedules_created += 1
            except IntegrityError as e:
                print(f"  ✗ Error creating schedule for {parish}: {e}")
                continue

    if schedules_created > 0:
        print(f"  ✓ Created {schedules_created} schedules for {parish}")

print("\nImport completed!")
