import json

from missas.core.models import Contact, Parish

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

with open("./natal_contacts.jsonl") as f:
    datas = [json.loads(line) for line in f.readlines()]


for d in datas:
    parish_name = d.pop("parish_name")

    if not parish_name:
        print(f"No parish_name for: {d}")
        continue

    cleaned_parish_name = NAMES_MAPPER.get(parish_name, parish_name)
    cleaned_parish_name = (
        cleaned_parish_name.replace("’", "'").split("–")[0].split("-")[0].strip()
    )

    try:
        parish = Parish.objects.get(name__contains=cleaned_parish_name)
    except Parish.DoesNotExist:
        print(f"'{parish_name}': '',")
        continue
    except Parish.MultipleObjectsReturned:
        print(f"'{parish_name}': '',")
        continue

    try:
        parish.contact = Contact.objects.create(**d)
    except TypeError:
        print(f"TypeError for {d}")
        continue

    parish.save()
