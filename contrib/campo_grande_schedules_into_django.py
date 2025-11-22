import json
import os
from datetime import datetime

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Parish, Schedule, Source, State  # noqa

DAY_MAPPING = {
    "domingo": Schedule.Day.SUNDAY,
    "segunda-feira": Schedule.Day.MONDAY,
    "terça-feira": Schedule.Day.TUESDAY,
    "quarta-feira": Schedule.Day.WEDNESDAY,
    "quinta-feira": Schedule.Day.THURSDAY,
    "sexta-feira": Schedule.Day.FRIDAY,
    "sábado": Schedule.Day.SATURDAY,
}

TYPE_MAPPING = {
    "missa": Schedule.Type.MASS,
    "confissão": Schedule.Type.CONFESSION,
    "confissao": Schedule.Type.CONFESSION,
}

with open("./contrib/campo_grande_schedules.jsonl") as f:
    schedules_data = [json.loads(line) for line in f.readlines()]

source, _ = Source.objects.get_or_create(
    type=Source.Type.SITE,
    link="https://arquidiocesedecampogrande.org.br/horarios-de-missas/",
    defaults={"description": "Site da Arquidiocese de Campo Grande"},
)

try:
    state = State.objects.get(short_name="MS")
except State.DoesNotExist:
    print("ERROR: State 'MS' (Mato Grosso do Sul) not found in database.")
    print("Please create the state first using Django admin or fixtures.")
    exit(1)

city, _ = City.objects.get_or_create(
    slug="campo-grande",
    state=state,
    defaults={"name": "Campo Grande"},
)

created_count = 0
skipped_count = 0
error_count = 0

for data in schedules_data:
    parish_name = data["parish_name"].strip()

    if parish_name.startswith("PARÓQUIA "):
        parish_name = parish_name.replace("PARÓQUIA ", "Paróquia ")
    elif parish_name.startswith("CAPELANIA "):
        parish_name = parish_name.replace("CAPELANIA ", "Capelania ")
    elif parish_name.startswith("Capela "):
        pass
    else:
        parish_name = f"Paróquia {parish_name}"

    parish, parish_created = Parish.objects.get_or_create(
        city=city,
        slug=slugify(parish_name),
        defaults={"name": parish_name},
    )

    if parish_created:
        print(f"✓ Parish created: {parish}")

    day_str = data["day"].strip().lower()
    day = DAY_MAPPING.get(day_str)

    if not day and day != 0:
        print(f"⚠ Skipping - unknown day '{data['day']}' for {parish_name}")
        skipped_count += 1
        continue

    try:
        start_time = datetime.strptime(data["time"].strip(), "%H:%M").time()
    except ValueError:
        print(f"⚠ Skipping - invalid time '{data['time']}' for {parish_name}")
        skipped_count += 1
        continue

    schedule_type = TYPE_MAPPING.get(data["type"].strip().lower(), Schedule.Type.MASS)

    observation = data.get("notes", "")
    if observation:
        observation = observation.strip()

    try:
        schedule, created = Schedule.objects.get_or_create(
            parish=parish,
            day=day,
            start_time=start_time,
            defaults={
                "type": schedule_type,
                "observation": observation,
                "source": source,
            },
        )

        if created:
            created_count += 1
            print(f"  ✓ Schedule created: {schedule}")
        else:
            skipped_count += 1

    except IntegrityError as e:
        print(f"✗ Error creating schedule for {parish_name}: {e}")
        error_count += 1
        continue

print("\n" + "=" * 50)
print(f"Summary:")
print(f"  Created: {created_count} schedules")
print(f"  Skipped: {skipped_count} schedules")
print(f"  Errors: {error_count} schedules")
print("=" * 50)
