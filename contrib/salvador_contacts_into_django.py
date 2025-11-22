import json
import os

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import Contact, City, Parish  # noqa


JSONL_FILE = "./contrib/salvador_contacts.jsonl"


def normalize_parish_name(name):
    """Normalize parish name by removing extra information."""
    if not name:
        return ""

    name = name.replace("'", "'")

    # Remove " | Arquidiocese de São Salvador da Bahia" suffix if present
    if "|" in name:
        name = name.split("|")[0].strip()

    # Remove "Paróquia" prefix for cleaner matching
    if name.startswith("Paróquia "):
        name = name[9:]  # len("Paróquia ") = 9

    # Remove "Basílica" prefix for cleaner matching
    if name.startswith("Basílica "):
        name = name[9:]  # len("Basílica ") = 9

    return name.strip()


def get_or_create_parish(city, parish_name):
    """Get or create a parish in Salvador."""
    normalized_name = normalize_parish_name(parish_name)

    if not normalized_name:
        return None, False

    full_name = f"Paróquia {normalized_name}"

    # Try to find existing parish by exact match
    try:
        parish = Parish.objects.get(city=city, name=full_name)
        return parish, False
    except Parish.DoesNotExist:
        pass

    # Try to find by contains
    try:
        parish = Parish.objects.get(city=city, name__icontains=normalized_name)
        return parish, False
    except Parish.DoesNotExist:
        pass
    except Parish.MultipleObjectsReturned:
        print(f"Multiple parishes found for: {normalized_name}")
        return None, False

    # Create new parish
    parish, created = Parish.objects.get_or_create(
        city=city, name=full_name, defaults={"slug": slugify(full_name)}
    )

    return parish, created


def import_contacts():
    """Import Salvador contacts from JSONL file."""
    if not os.path.exists(JSONL_FILE):
        print(f"File not found: {JSONL_FILE}")
        print("Please run the scraper first:")
        print(
            f"  poetry run scrapy runspider contrib/scraper_salvador.py -o {JSONL_FILE}"
        )
        return

    # Get Salvador city
    try:
        city = City.objects.get(name="Salvador", state__short_name="BA")
    except City.DoesNotExist:
        print("City 'Salvador/BA' not found in database.")
        print("Please create the city first.")
        return

    # Read JSONL file
    with open(JSONL_FILE) as f:
        datas = [json.loads(line) for line in f.readlines()]

    print(f"Found {len(datas)} parishes in {JSONL_FILE}")

    created_parishes = 0
    created_contacts = 0
    skipped = 0
    errors = 0

    for d in datas:
        parish_name = d.get("parish_name")
        if not parish_name:
            print(f"Skipping entry without parish_name: {d}")
            skipped += 1
            continue

        # Get or create parish
        parish, parish_created = get_or_create_parish(city, parish_name)
        if not parish:
            print(f"Could not get or create parish: {parish_name}")
            skipped += 1
            continue

        if parish_created:
            print(f"✓ Created parish: {parish}")
            created_parishes += 1

        # Create or update contact
        try:
            contact, contact_created = Contact.objects.update_or_create(
                parish=parish,
                defaults={
                    "email": d.get("email", ""),
                    "facebook": d.get("facebook", ""),
                    "instagram": d.get("instagram", ""),
                    "phone": d.get("phone", ""),
                    "phone2": d.get("phone2", ""),
                    "whatsapp": d.get("whatsapp", ""),
                },
            )

            if contact_created:
                print(f"✓ Created contact: {contact} for {parish}")
                created_contacts += 1
            else:
                print(f"↻ Updated contact for {parish}")

        except IntegrityError as e:
            print(f"✗ IntegrityError for {parish_name}: {e}")
            errors += 1
            continue
        except Exception as e:
            print(f"✗ Error for {parish_name}: {e}")
            errors += 1
            continue

    print("\n" + "=" * 60)
    print("Import Summary:")
    print(f"  Total entries processed: {len(datas)}")
    print(f"  Parishes created: {created_parishes}")
    print(f"  Contacts created: {created_contacts}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print("=" * 60)


if __name__ == "__main__":
    import_contacts()
