import json
import os

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import Contact, City, Parish  # noqa

NAMES_MAPPER = {
    "Paróquia de São José – Angicos": "",
    "Paróquia de São Francisco de Assis – Pedro Velho": "",
    "Paróquia de São Francisco de Assis – Lagoa de Pedras": "",
    "Paróquia do Santo André de Soveral – Jardim Aeroporto": "Santo André de Soveral",
    "Paróquia de Nossa Sra. dos Impossíveis – Pitimbu – Natal": "Paróquia de Nossa Senhora dos Impossíveis",
    "Paróquia do Santo Ambrósio Francisco Ferro – Planalto": "Paróquia de Santo Ambrósio Francisco Ferro",
    "Paróquia de São José – Cidade Nova – Natal": "",
    "Paróquia do Santuário dos Santos Mártires de Cunhaú e Uruaçu – Nazaré – Natal": "",
    "Paróquia Jesus Bom Pastor – Bom Pastor – Natal": "Paróquia de Jesus Bom Pastor",
    "Paróquia de São Francisco de Assis – Cidade Satélite – Natal": "",
    "Paróquia do Sagrado Coração de Jesus    e Nossa Senhora do Perpétuo Socorro – Morro Branco - Natal": "Paróquia de Nossa Senhora do Perpétuo Socorro",
    "Paróquia de Santa Rita de Cássia dos Impossíveis – Ponta Negra – Natal": "Paróquia de Santa Rita de Cássia",
    "Paróquia de Nossa Senhora das Graças e Santa Teresinha – Tirol – Natal": "Paróquia de Santa Teresinha",
    "Paróquia da Catedral de Nossa Senhora da Apresentação - Natal": "Paróquia de Nossa Senhora da Apresentação",
    "Paróquia Santuário de Nossa Senhora de Fátima – Parque das Dunas – Natal": "",
    "Paróquia de São Gonçalo do Amarante": "Paróquia de São Gonçalo",
    "Paróquia da Virgem e Mártir Santa Luzia - Touros": "",
    "Paróquia de São José – São José de Campestre": "",
}

with open("./contrib/natal_contacts.jsonl") as f:
    datas = [json.loads(line) for line in f.readlines()]


for d in datas:
    if "city" not in d:
        continue

    name = d["parish_name"].replace("’", "'").split("–")[0].split("-")[0].strip()

    try:
        name = NAMES_MAPPER.get(name, name)
        city = City.objects.get(
            name=d["city"].replace("’", "'"), state__short_name="RN"
        )
    except City.DoesNotExist:
        city = City.objects.get(
            name__icontains=d["city"].replace("’", "'"), state__short_name="RN"
        )

    if d["city"] == "Natal":
        try:
            parish = Parish.objects.get(city=city, name__contains=name)
        except Parish.DoesNotExist:
            print(f"'{name}': '',")
            continue
        except Parish.MultipleObjectsReturned:
            print(f"'{name}': '',")
            continue
    else:
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
