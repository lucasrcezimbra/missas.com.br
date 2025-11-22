import json
import os

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Parish, Source  # noqa

JSONL_FILE = "./contrib/curitiba_parishes.jsonl"

NAMES_MAPPER = {}

city = City.objects.get(name="Curitiba", state__short_name="PR")

source, _ = Source.objects.get_or_create(
    type=Source.Type.SITE,
    link="https://arquidiocesedecuritiba.org.br/paroquias/",
    defaults={"description": "Arquidiocese de Curitiba - Lista de Paróquias"},
)

with open(JSONL_FILE) as f:
    datas = [json.loads(line) for line in f.readlines()]

for d in datas:
    name = d["parish_name"].strip()

    name = NAMES_MAPPER.get(name, name)

    try:
        parish, created = Parish.objects.get_or_create(
            city=city,
            slug=slugify(name),
            defaults={"name": name},
        )

        if created:
            print(f"Created: {parish}")
        else:
            print(f"Already exists: {parish}")

    except IntegrityError as e:
        print(f"Error creating {name}: {e}")
        continue

print(f"\nProcessed {len(datas)} parishes from {JSONL_FILE}")
print(f"Total parishes in Curitiba: {Parish.objects.filter(city=city).count()}")
