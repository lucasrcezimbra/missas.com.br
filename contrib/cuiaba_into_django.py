import json
import os
import re
from datetime import date

import django
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Parish, Schedule, Source  # noqa

DAY_MAPPING = {
    "segunda-feira": Schedule.Day.MONDAY,
    "terça-feira": Schedule.Day.TUESDAY,
    "quarta-feira": Schedule.Day.WEDNESDAY,
    "quinta-feira": Schedule.Day.THURSDAY,
    "sexta-feira": Schedule.Day.FRIDAY,
    "sábado": Schedule.Day.SATURDAY,
    "domingo": Schedule.Day.SUNDAY,
}


def parse_time(time_str):
    """Convert time strings like '6h30', '19h', '7h e 18h' to time format."""
    time_str = time_str.strip().lower()

    if time_str in ["não tem", "não há celebração"]:
        return []

    times = []
    for part in re.split(r'[/,]|\s+e\s+|\s+-\s+', time_str):
        part = part.strip()
        if not part or part in ["não tem", "não há celebração"]:
            continue

        match = re.match(r'(\d+)h(\d+)?', part)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            times.append(f"{hour:02d}:{minute:02d}")

    return times


with open("./contrib/cuiaba_output.jsonl") as f:
    datas = [json.loads(line) for line in f.readlines()]

city = City.objects.get(name="Cuiabá", state__short_name="MT")

source, created = Source.objects.get_or_create(
    type=Source.Type.SITE,
    link="https://arquidiocesecuiaba.org.br/horarios-de-missas/",
    defaults={"description": "Site da Arquidiocese de Cuiabá"},
)

if created:
    print(f"Source created: {source}")

for data in datas:
    parish_name = data["parish_name"]

    parish, created = Parish.objects.get_or_create(
        city=city,
        slug=slugify(parish_name),
        defaults={"name": parish_name},
    )

    if created:
        print(f"Parish created: {parish}")

    for schedule_item in data["schedule_data"]:
        tipo = schedule_item["tipo"]
        dia_semana = schedule_item["dia_da_semana"].lower()
        horario = schedule_item["horario"]

        schedule_type = Schedule.Type.MASS if "missa" in tipo.lower() else Schedule.Type.CONFESSION

        day = DAY_MAPPING.get(dia_semana)
        if day is None:
            print(f"Unknown day: {dia_semana} for {parish_name}")
            continue

        times = parse_time(horario)

        for time_str in times:
            schedule, created = Schedule.objects.get_or_create(
                parish=parish,
                day=day,
                start_time=time_str,
                defaults={
                    "type": schedule_type,
                    "source": source,
                    "verified_at": date.today(),
                },
            )

            if created:
                print(f"Schedule created: {schedule}")
            else:
                schedule.type = schedule_type
                schedule.source = source
                schedule.verified_at = date.today()
                schedule.save()
                print(f"Schedule updated: {schedule}")

print("Import completed!")
