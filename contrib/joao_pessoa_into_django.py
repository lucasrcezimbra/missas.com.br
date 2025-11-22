"""
Import João Pessoa (PB) parish data into Django models.

This script reads the scraped parish data from joao_pessoa_parishes.jsonl
and creates/updates the corresponding Django model instances:
- State (Paraíba/PB)
- Cities
- Parishes
- Contacts (phone, email)

Requirements:
- Django environment must be properly configured
- Database must be migrated
- Required environment variables must be set (see .env or settings.py)

Usage:
    # In development with proper database setup:
    poetry run python contrib/joao_pessoa_into_django.py

    # Or via Django shell:
    poetry run python manage.py shell < contrib/joao_pessoa_into_django.py

The script will:
1. Create the Paraíba (PB) state if it doesn't exist
2. Create all cities mentioned in the parish data
3. Create parishes with cleaned names (removing prefixes like "Paróquia")
4. Create or update contact information for each parish

Statistics will be printed at the end showing:
- Number of cities created/existing
- Number of parishes created/existing
- Number of contacts created/updated
- Any errors encountered
"""

import json
import os
import sys

import django
from django.utils.text import slugify

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Contact, Parish, State  # noqa: E402


def clean_phone(phone):
    """Clean phone number to keep only digits and parentheses/dashes."""
    if not phone:
        return ""
    return phone.strip()


def main():
    # Create or get Paraíba state
    state, created = State.objects.get_or_create(
        short_name="PB",
        defaults={
            "name": "Paraíba",
            "slug": "paraiba",
        },
    )
    if created:
        print(f"✓ Created state: {state}")
    else:
        print(f"→ State already exists: {state}")

    # Read the scraped data
    jsonl_file = "./contrib/joao_pessoa_parishes.jsonl"
    with open(jsonl_file) as f:
        parishes_data = [json.loads(line) for line in f.readlines()]

    print(f"\n→ Found {len(parishes_data)} parishes to import\n")

    stats = {
        "cities_created": 0,
        "cities_existing": 0,
        "parishes_created": 0,
        "parishes_existing": 0,
        "contacts_created": 0,
        "contacts_updated": 0,
        "errors": 0,
    }

    for data in parishes_data:
        try:
            # Skip if missing required fields
            if not data.get("parish_name") or not data.get("city"):
                print(f"⚠ Skipping entry - missing parish_name or city: {data}")
                stats["errors"] += 1
                continue

            # Get or create city
            city_name = data["city"].strip()
            city, created = City.objects.get_or_create(
                name=city_name,
                state=state,
                defaults={"slug": slugify(city_name)},
            )
            if created:
                print(f"  ✓ Created city: {city}")
                stats["cities_created"] += 1
            else:
                stats["cities_existing"] += 1

            # Clean parish name
            parish_name = data["parish_name"].strip()
            # Remove common prefixes for cleaner names
            parish_name = (
                parish_name.replace("label_important", "")
                .replace("Paróquia ", "")
                .replace("Santuário ", "")
                .replace("Capelania ", "")
                .strip()
            )

            # Get or create parish
            parish_slug = slugify(parish_name)
            parish, created = Parish.objects.get_or_create(
                city=city,
                slug=parish_slug,
                defaults={"name": parish_name},
            )
            if created:
                print(f"  ✓ Created parish: {parish}")
                stats["parishes_created"] += 1
            else:
                stats["parishes_existing"] += 1

            # Get or create contact
            phone = ""
            phone2 = ""
            if "phones" in data and data["phones"]:
                phones = data["phones"]
                if len(phones) > 0:
                    phone = clean_phone(phones[0])
                if len(phones) > 1:
                    phone2 = clean_phone(phones[1])

            email = ""
            if "emails" in data and data["emails"]:
                email = data["emails"][0].strip()

            # Try to get existing contact or create new one
            try:
                contact = Contact.objects.get(parish=parish)
                # Update existing contact
                contact_updated = False
                if phone and not contact.phone:
                    contact.phone = phone
                    contact_updated = True
                if phone2 and not contact.phone2:
                    contact.phone2 = phone2
                    contact_updated = True
                if email and not contact.email:
                    contact.email = email
                    contact_updated = True

                if contact_updated:
                    contact.save()
                    print(f"    → Updated contact for {parish}")
                    stats["contacts_updated"] += 1

            except Contact.DoesNotExist:
                # Create new contact
                if phone or email:
                    contact = Contact.objects.create(
                        parish=parish,
                        phone=phone,
                        phone2=phone2,
                        email=email,
                    )
                    print(f"    ✓ Created contact for {parish}")
                    stats["contacts_created"] += 1

        except Exception as e:
            print(f"✗ Error processing {data.get('parish_name', 'unknown')}: {e}")
            stats["errors"] += 1
            continue

    # Print summary
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"State: {state}")
    print(f"Cities created: {stats['cities_created']}")
    print(f"Cities (existing): {stats['cities_existing']}")
    print(f"Parishes created: {stats['parishes_created']}")
    print(f"Parishes (existing): {stats['parishes_existing']}")
    print(f"Contacts created: {stats['contacts_created']}")
    print(f"Contacts updated: {stats['contacts_updated']}")
    print(f"Errors: {stats['errors']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
