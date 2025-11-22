"""
Import Curitiba Mass schedules into Django.

This script processes scraped data from the Curitiba spider and creates
Parish and Schedule records in the database.

Prerequisites:
- The scraper must be enhanced with JavaScript rendering to extract schedule data
- Run the scraper first: poetry run scrapy runspider contrib/scraper_curitiba.py -o contrib/curitiba_schedules.jsonl
- Ensure Curitiba city exists in the database

Expected JSONL format:
{
    "parish_name": "Paróquia São Francisco de Paula",
    "parish_url": "https://...",
    "slug": "paroquia-sao-francisco-de-paula",
    "days": "Terça-feira, Quarta-feira, Quinta-feira, Sexta-feira",
    "times": "18:30"
}
"""

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

JSONL_FILE = "./contrib/curitiba_schedules.jsonl"

NAMES_MAPPER = {}

DAY_MAPPING = {
    "domingo": Schedule.Day.SUNDAY,
    "segunda-feira": Schedule.Day.MONDAY,
    "segunda": Schedule.Day.MONDAY,
    "terça-feira": Schedule.Day.TUESDAY,
    "terça": Schedule.Day.TUESDAY,
    "quarta-feira": Schedule.Day.WEDNESDAY,
    "quarta": Schedule.Day.WEDNESDAY,
    "quinta-feira": Schedule.Day.THURSDAY,
    "quinta": Schedule.Day.THURSDAY,
    "sexta-feira": Schedule.Day.FRIDAY,
    "sexta": Schedule.Day.FRIDAY,
    "sábado": Schedule.Day.SATURDAY,
}


def parse_time(time_str):
    """Parse time string like '18:30' or '09:00' into time object."""
    time_str = time_str.strip()
    match = re.match(r"(\d{1,2}):(\d{2})", time_str)
    if match:
        hour, minute = match.groups()
        return time(int(hour), int(minute))
    return None


def parse_days(days_str):
    """Parse days string into list of Schedule.Day values."""
    if not days_str:
        return []

    days_str = days_str.lower()
    days = []

    for day_name, day_value in DAY_MAPPING.items():
        if day_name in days_str:
            days.append(day_value)

    return days


city = City.objects.get(name="Curitiba", state__short_name="PR")

source, _ = Source.objects.get_or_create(
    type=Source.Type.SITE,
    link="https://arquidiocesedecuritiba.org.br/paroquias/",
    defaults={"description": "Arquidiocese de Curitiba - Horários de Missas"},
)

with open(JSONL_FILE) as f:
    datas = [json.loads(line) for line in f.readlines()]

created_parishes = 0
created_schedules = 0
skipped_schedules = 0

for d in datas:
    if d.get("note") == "Schedule data requires JavaScript rendering":
        continue

    name = d["parish_name"].strip()
    name = NAMES_MAPPER.get(name, name)

    parish, created = Parish.objects.get_or_create(
        city=city,
        slug=slugify(name),
        defaults={"name": name},
    )

    if created:
        created_parishes += 1
        print(f"Created parish: {parish}")

    days_list = parse_days(d.get("days", ""))
    times_str = d.get("times", "")

    if not days_list or not times_str:
        skipped_schedules += 1
        continue

    times = [t.strip() for t in times_str.split(",")]

    for day in days_list:
        for time_str in times:
            start_time = parse_time(time_str)
            if not start_time:
                print(f"Warning: Could not parse time '{time_str}' for {parish}")
                continue

            try:
                schedule, created = Schedule.objects.get_or_create(
                    parish=parish,
                    day=day,
                    start_time=start_time,
                    defaults={
                        "type": Schedule.Type.MASS,
                        "source": source,
                    },
                )

                if created:
                    created_schedules += 1
                    print(f"Created schedule: {schedule}")

            except IntegrityError as e:
                print(f"Error creating schedule for {parish}: {e}")
                continue

print("\n=== Summary ===")
print(f"Processed {len(datas)} records from {JSONL_FILE}")
print(f"Created {created_parishes} new parishes")
print(f"Created {created_schedules} new schedules")
print(f"Skipped {skipped_schedules} records without schedule data")
print(
    f"Total parishes in Curitiba: {Parish.objects.filter(city=city).count()}"
)
print(
    f"Total schedules in Curitiba: {Schedule.objects.filter(parish__city=city).count()}"
)
