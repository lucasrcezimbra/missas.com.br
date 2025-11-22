import json
import os
import re

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Contact, Parish, Source, State  # noqa


def extract_phone(times):
    """Extract phone number from times array."""
    for item in times:
        if item.startswith("Telefone:"):
            phone = item.replace("Telefone:", "").strip()
            phone = re.sub(r"[^\d+]", "", phone)
            if phone and not phone.startswith("+"):
                phone = "+55" + phone
            return phone
    return ""


def extract_email(times):
    """Extract email from times array."""
    for i, item in enumerate(times):
        if item.strip() == "E-mail:" and i + 1 < len(times):
            next_item = times[i + 1].strip()
            if "@" in next_item:
                email = next_item.replace("[email protected]", "@")
                return email
    return ""


def extract_address(times):
    """Extract address from times array."""
    for item in times:
        if item.startswith("Endereço:"):
            return item.replace("Endereço:", "").strip()
    return ""


with open("./contrib/manaus.jsonl") as f:
    datas = [json.loads(line) for line in f.readlines()]

# Get or create state and city
state, _ = State.objects.get_or_create(
    short_name="AM",
    defaults={"name": "Amazonas", "slug": "amazonas"}
)

city, _ = City.objects.get_or_create(
    name="Manaus",
    state=state,
    defaults={"slug": "manaus"}
)

# Create source
source, _ = Source.objects.get_or_create(
    link="https://arquidiocesedemanaus.org.br/paroquias/",
    defaults={
        "description": "Arquidiocese de Manaus - Paróquias",
        "type": Source.Type.SITE,
    }
)

created_parishes = 0
updated_parishes = 0
created_contacts = 0
updated_contacts = 0

for d in datas:
    parish_name = d["parish_name"].strip()
    times = d.get("times", [])

    # Clean parish name
    parish_name = parish_name.replace("'", "'")

    # Create or get parish
    parish, created = Parish.objects.get_or_create(
        city=city,
        slug=slugify(parish_name),
        defaults={"name": parish_name}
    )

    if created:
        created_parishes += 1
        print(f"✓ Created parish: {parish}")
    else:
        updated_parishes += 1

    # Extract contact information
    phone = extract_phone(times)
    email = extract_email(times)
    address = extract_address(times)

    # Create or update contact
    if phone or email:
        try:
            contact, created = Contact.objects.update_or_create(
                parish=parish,
                defaults={
                    "phone": phone,
                    "email": email,
                }
            )
            if created:
                created_contacts += 1
                print(f"  ✓ Created contact for {parish.name}")
            else:
                updated_contacts += 1
                print(f"  ↻ Updated contact for {parish.name}")
        except IntegrityError as e:
            print(f"  ✗ Error creating contact for {parish.name}: {e}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Parishes created: {created_parishes}")
print(f"Parishes updated: {updated_parishes}")
print(f"Contacts created: {created_contacts}")
print(f"Contacts updated: {updated_contacts}")
print(f"Source: {source}")
