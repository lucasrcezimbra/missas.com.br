import json
import os

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Contact, Parish  # noqa


JSONL_FILE = "./contrib/sao_luis_unified.jsonl"

with open(JSONL_FILE) as f:
    datas = [json.loads(line) for line in f.readlines()]


for d in datas:
    parish_name = d.get("parish_name", "").strip()
    if not parish_name:
        print(f"Skipping entry without parish_name: {d.get('parish_id')}")
        continue

    parish_name = parish_name.replace("'", "'").strip()

    contact_info = d.get("contact_info", {})
    city_name = contact_info.get("city", "São Luís")

    try:
        city = City.objects.get(name=city_name, state__short_name="MA")
    except City.DoesNotExist:
        try:
            city = City.objects.get(name__icontains=city_name, state__short_name="MA")
        except City.DoesNotExist:
            print(f"City not found: {city_name}. Using São Luís as default.")
            city = City.objects.get(name="São Luís", state__short_name="MA")

    parish, parish_created = Parish.objects.get_or_create(
        city=city, name=parish_name, defaults={"slug": slugify(parish_name)}
    )

    if parish_created:
        print(f"✓ Parish created: {parish}")

    if contact_info:
        try:
            contact, contact_created = Contact.objects.update_or_create(
                parish=parish,
                defaults={
                    "email": contact_info.get("email", ""),
                    "facebook": contact_info.get("facebook", ""),
                    "instagram": contact_info.get("instagram", ""),
                    "phone": contact_info.get("phone", ""),
                    "phone2": contact_info.get("phone2", ""),
                    "whatsapp": contact_info.get("whatsapp", ""),
                },
            )
            if contact_created:
                print(f"  ✓ Contact created: {contact}")
            else:
                print(f"  ✓ Contact updated: {contact}")
        except IntegrityError as e:
            print(f"  ✗ Contact error for {parish}: {e}")
            continue

print("\n✅ Import completed!")
