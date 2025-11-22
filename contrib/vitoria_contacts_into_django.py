import json
import os

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import Contact, City, Parish  # noqa

NAMES_MAPPER = {}

with open("./contrib/vitoria_parishes.jsonl") as f:
    datas = [json.loads(line) for line in f.readlines()]


for d in datas:
    if "city" not in d:
        continue

    name = d["parish_name"].replace("'", "'").split("–")[0].split("-")[0].strip()

    try:
        name = NAMES_MAPPER.get(name, name)
        city = City.objects.get(
            name=d["city"].replace("'", "'"), state__short_name="ES"
        )
    except City.DoesNotExist:
        city = City.objects.get(
            name__icontains=d["city"].replace("'", "'"), state__short_name="ES"
        )

    parish, created = Parish.objects.get_or_create(
        city=city, name=name, slug=slugify(name)
    )

    if created:
        print(f"{parish} created")

    try:
        contact, created = Contact.objects.get_or_create(
            email=d.get("email", ""),
            facebook=d.get("facebook", ""),
            instagram=d.get("instagram", ""),
            phone=d.get("phone", ""),
            phone2=d.get("phone2", ""),
            whatsapp=d.get("whatsapp", ""),
            parish=parish,
        )
    except IntegrityError:
        print(d)
        continue

    if created:
        print(f"{contact} created")
