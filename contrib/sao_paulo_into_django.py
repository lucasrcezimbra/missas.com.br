import json
import os

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Contact, Parish, State  # noqa


def import_sao_paulo_data(jsonl_file):
    """Import scraped São Paulo archdiocese data into Django models."""

    state, _ = State.objects.get_or_create(
        short_name="SP",
        defaults={
            "name": "São Paulo",
            "slug": "sao-paulo",
        },
    )

    city, _ = City.objects.get_or_create(
        name="São Paulo",
        state=state,
        defaults={"slug": "sao-paulo"},
    )

    with open(jsonl_file) as f:
        data_items = [json.loads(line) for line in f.readlines()]

    created_parishes = 0
    updated_parishes = 0
    created_contacts = 0
    updated_contacts = 0
    errors = []

    for data in data_items:
        parish_name = data.get("parish_name", "").strip()

        if not parish_name:
            errors.append({"error": "Missing parish name", "data": data})
            continue

        parish_name = parish_name.replace("'", "'")

        parish_slug = slugify(parish_name)

        parish, parish_created = Parish.objects.get_or_create(
            city=city,
            slug=parish_slug,
            defaults={"name": parish_name},
        )

        if parish_created:
            created_parishes += 1
            print(f"✓ Created parish: {parish}")
        else:
            if parish.name != parish_name:
                parish.name = parish_name
                parish.save()
                updated_parishes += 1
                print(f"↻ Updated parish name: {parish}")

        contact_data = {
            "email": data.get("email", "") or "",
            "facebook": data.get("facebook", "") or "",
            "instagram": data.get("instagram", "") or "",
            "phone": data.get("phone", "") or "",
            "phone2": data.get("phone2", "") or "",
            "whatsapp": data.get("whatsapp", "") or "",
        }

        has_contact_info = any(contact_data.values())

        if has_contact_info:
            try:
                contact, contact_created = Contact.objects.update_or_create(
                    parish=parish,
                    defaults=contact_data,
                )

                if contact_created:
                    created_contacts += 1
                    print(f"  ✓ Created contact for {parish.name}")
                else:
                    updated_contacts += 1
                    print(f"  ↻ Updated contact for {parish.name}")

            except IntegrityError as e:
                errors.append(
                    {
                        "error": f"IntegrityError: {e}",
                        "parish": parish_name,
                        "data": contact_data,
                    }
                )
                print(f"  ✗ Error creating contact for {parish.name}: {e}")

    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"Parishes created: {created_parishes}")
    print(f"Parishes updated: {updated_parishes}")
    print(f"Contacts created: {created_contacts}")
    print(f"Contacts updated: {updated_contacts}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")

    print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: poetry run python contrib/sao_paulo_into_django.py <jsonl_file>")
        print("Example: poetry run python contrib/sao_paulo_into_django.py sao_paulo_parishes.jsonl")
        sys.exit(1)

    jsonl_file = sys.argv[1]

    if not os.path.exists(jsonl_file):
        print(f"Error: File '{jsonl_file}' not found")
        sys.exit(1)

    import_sao_paulo_data(jsonl_file)
