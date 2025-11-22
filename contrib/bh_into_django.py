import json
import os

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Parish  # noqa

# TODO: Update this path when scraper data becomes available
JSONL_FILE = "./contrib/bh.jsonl"

# TODO: Add name mappings if needed to handle parish name variations
# Example: "Paróquia de São José – Centro" -> "Paróquia de São José"
NAMES_MAPPER = {}

try:
    with open(JSONL_FILE) as f:
        datas = [json.loads(line) for line in f.readlines()]
except FileNotFoundError:
    print(f"Error: {JSONL_FILE} not found.")
    print(
        "Please run the BH scraper first: "
        "poetry run scrapy runspider contrib/scraper_bh.py -o contrib/bh.jsonl"
    )
    print(
        "\nNote: The scraper currently requires JavaScript rendering support "
        "to extract data from the BH website."
    )
    exit(1)

try:
    bh_city = City.objects.get(name="Belo Horizonte", state__short_name="MG")
except City.DoesNotExist:
    print("Error: Belo Horizonte/MG city not found in database.")
    print("Please ensure the city exists in the database before running this script.")
    exit(1)

print(f"Found city: {bh_city}")
print(f"Processing {len(datas)} entries...\n")

created_count = 0
updated_count = 0
skipped_count = 0

for d in datas:
    if not d.get("parish_name"):
        print(f"Skipping entry without parish_name: {d}")
        skipped_count += 1
        continue

    raw_name = d["parish_name"].replace("'", "'").strip()
    name = raw_name.split("–")[0].split("-")[0].strip()

    name = NAMES_MAPPER.get(name, name)

    if not name:
        print(f"Skipping empty parish name from: {raw_name}")
        skipped_count += 1
        continue

    try:
        parish, created = Parish.objects.get_or_create(
            city=bh_city, name=name, defaults={"slug": slugify(name)}
        )

        if created:
            print(f"✓ Created: {parish}")
            created_count += 1
        else:
            print(f"• Exists: {parish}")
            updated_count += 1

    except IntegrityError as e:
        print(f"✗ Error creating parish '{name}': {e}")
        skipped_count += 1
        continue

print("\n" + "=" * 80)
print(f"Summary:")
print(f"  Created: {created_count}")
print(f"  Already existed: {updated_count}")
print(f"  Skipped: {skipped_count}")
print(f"  Total processed: {created_count + updated_count + skipped_count}")
print("=" * 80)

# TODO: Parse and import schedule data from the 'times' field
# The 'times' field contains text like:
# ["Segunda a sexta-feira - 11h e 16h30", "Domingo - 7h, 11h e 19h"]
# This will require parsing the Portuguese text to extract:
# - Days of the week
# - Times
# - Creating Schedule objects
# Consider using an LLM (similar to import.py) for parsing unstructured text
