import json
import os

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Contact, Parish, State  # noqa

with open("./contrib/campo_grande_contacts.jsonl") as f:
    contacts_data = [json.loads(line) for line in f.readlines()]

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

created_parishes = 0
created_contacts = 0
skipped_count = 0
error_count = 0

for data in contacts_data:
    parish_name = (
        data["parish_name"]
        .replace(" - Arquidiocese de Campo Grande", "")
        .replace("'", "'")
        .strip()
    )

    if parish_name.startswith("PARÓQUIA "):
        parish_name = parish_name.replace("PARÓQUIA ", "Paróquia ")
    elif parish_name.startswith("SANTUÁRIO "):
        parish_name = parish_name.replace("SANTUÁRIO ", "Santuário ")
    elif parish_name.startswith("CAPELANIA "):
        parish_name = parish_name.replace("CAPELANIA ", "Capelania ")
    elif not parish_name.startswith(("Paróquia ", "Santuário ", "Capelania ")):
        parish_name = f"Paróquia {parish_name}"

    parish, parish_created = Parish.objects.get_or_create(
        city=city,
        slug=slugify(parish_name),
        defaults={"name": parish_name},
    )

    if parish_created:
        created_parishes += 1
        print(f"✓ Parish created: {parish}")

    email = data.get("email", "").strip() if data.get("email") else ""
    facebook = data.get("facebook", "").strip() if data.get("facebook") else ""
    instagram = data.get("instagram", "").strip() if data.get("instagram") else ""
    phone = data.get("phone", "").strip() if data.get("phone") else ""
    phone2 = data.get("phone2", "").strip() if data.get("phone2") else ""
    whatsapp = data.get("whatsapp", "").strip() if data.get("whatsapp") else ""

    if not any([email, facebook, instagram, phone, phone2, whatsapp]):
        print(f"⚠ Skipping - no contact info for {parish_name}")
        skipped_count += 1
        continue

    try:
        contact, created = Contact.objects.get_or_create(
            parish=parish,
            defaults={
                "email": email,
                "facebook": facebook,
                "instagram": instagram,
                "phone": phone,
                "phone2": phone2,
                "whatsapp": whatsapp,
            },
        )

        if created:
            created_contacts += 1
            print(f"  ✓ Contact created: {contact} for {parish_name}")
        else:
            skipped_count += 1
            print(f"  ⊙ Contact exists for {parish_name}")

    except IntegrityError as e:
        print(f"✗ Error creating contact for {parish_name}: {e}")
        error_count += 1
        continue

print("\n" + "=" * 50)
print(f"Summary:")
print(f"  Created: {created_parishes} parishes, {created_contacts} contacts")
print(f"  Skipped: {skipped_count} items")
print(f"  Errors: {error_count} items")
print("=" * 50)
