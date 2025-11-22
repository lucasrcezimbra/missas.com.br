import json
import os
import re

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Parish, Source, State  # noqa


def extract_city_from_parish_name(parish_name):
    """Extract city name from parish name if present."""
    patterns = [
        r"-\s*([A-Za-zÀ-ÿ\s]+)\s*-\s*Arquidiocese",
        r"\(([A-Za-zÀ-ÿ\s]+)\)\s*-\s*Arquidiocese",
    ]

    for pattern in patterns:
        match = re.search(pattern, parish_name)
        if match:
            city_name = match.group(1).strip()
            if city_name and city_name not in ["Centro", "Palhoça"]:
                return city_name

    return None


def clean_parish_name(parish_name):
    """Remove Arquidiocese suffix and extra whitespace."""
    name = re.sub(r"\s*-\s*Arquidiocese de Florianópolis\s*$", "", parish_name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


with open("./contrib/florianopolis.jsonl") as f:
    datas = [json.loads(line) for line in f if line.strip()]

state, _ = State.objects.get_or_create(
    short_name="SC",
    defaults={
        "name": "Santa Catarina",
        "slug": "santa-catarina",
    },
)
print(f"State: {state}")

default_city, _ = City.objects.get_or_create(
    name="Florianópolis",
    state=state,
    defaults={"slug": slugify("Florianópolis")},
)
print(f"Default city: {default_city}")

source, _ = Source.objects.get_or_create(
    type=Source.Type.SITE,
    link="https://arquifln.org.br/paroquias",
    defaults={"description": "Site da Arquidiocese de Florianópolis"},
)
print(f"Source: {source}")

created_count = 0
updated_count = 0
error_count = 0

for d in datas:
    parish_name_raw = d.get("parish_name", "")
    if not parish_name_raw:
        print(f"Skipping entry without parish name: {d}")
        error_count += 1
        continue

    parish_name = clean_parish_name(parish_name_raw)

    city_name = extract_city_from_parish_name(parish_name_raw)

    if city_name:
        city, city_created = City.objects.get_or_create(
            name=city_name,
            state=state,
            defaults={"slug": slugify(city_name)},
        )
        if city_created:
            print(f"  Created city: {city}")
    else:
        city = default_city

    try:
        parish, created = Parish.objects.get_or_create(
            city=city,
            slug=slugify(parish_name),
            defaults={"name": parish_name},
        )

        if created:
            print(f"✓ Created: {parish}")
            created_count += 1
        else:
            if parish.name != parish_name:
                parish.name = parish_name
                parish.save()
                print(f"↻ Updated: {parish}")
                updated_count += 1
            else:
                print(f"- Exists: {parish}")

    except IntegrityError as e:
        print(f"✗ Error creating parish '{parish_name}': {e}")
        error_count += 1
        continue

print("\n" + "=" * 80)
print(f"Summary:")
print(f"  Created: {created_count} parishes")
print(f"  Updated: {updated_count} parishes")
print(f"  Errors: {error_count}")
print(f"  Total processed: {len(datas)}")
print("=" * 80)

print("\nNote: Schedule data from 'times' field needs to be parsed separately.")
print("The 'times' field contains mixed content (schedules, history, contact info).")
print("Consider using LLM or manual review to extract actual mass/confession times.")
