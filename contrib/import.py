import os
from textwrap import dedent

import django
import jsonstar as json
import llm
from datadiff import diff
from decouple import config
from django.forms.models import model_to_dict
from django.utils.dateparse import parse_time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import Contact, City, Parish, Schedule, Source  # noqa

WHATSAPP = "+5584994766014"
MESSAGE = """
[Message at 2024-09-16]
Bom dia. Qual o horário das missas na paróquia?
[Message at 2024-09-16]
Boa tarde
Hoje  dia 16 em especial celebra a missa votiva de nossa senhora do Carmo às 19:30
Segundas, quartas, sextas e sábados às 06:00 horas
Tercas, quartas e sábados às 19:30 horas
Domingo 07:00, 09:00 e 18:00 hrs.
Prineira quinta do mês missa por cura é liberação
Primeira sexta feira missa só sagrado coração de Jesus
Dia 16 missa votiva de nossa senhora do Carmo
Todas às quartas grupo de oração Monte Carmelo
Todas as quintas exposição do Santíssimo às 15:00 adoração até às 18h e encerra com a benção do Santíssimo.
"""

contact = Contact.objects.get(whatsapp=WHATSAPP)
print(f"{contact=}")

parish = contact.parish
print(f"{parish=}")

source = Source.objects.get(type=Source.Type.WHATSAPP)
print(f"{source=}")

model = llm.get_model("gpt-4o")
model.key = config("OPENAI_API_KEY")

ai_response = model.prompt(
    MESSAGE,
    system=dedent(
        """\
        You are a Django management tool. You help to create new objects based on WhatsApp messages.
        This is the Django model:

        ```python
        class Schedule(models.Model):
            class Day(models.IntegerChoices):
                # It's integer to make the ordering easier
                SUNDAY = (0, "Domingo")
                MONDAY = (1, "Segunda-feira")
                TUESDAY = (2, "Terça-feira")
                WEDNESDAY = (3, "Quarta-feira")
                THURSDAY = (4, "Quinta-feira")
                FRIDAY = (5, "Sexta-feira")
                SATURDAY = (6, "Sábado")

            class Type(models.TextChoices):
                MASS = ("mass", "Missa")
                CONFESSION = ("confession", "Confissão")

            created_at = models.DateTimeField(auto_now_add=True)
            updated_at = models.DateTimeField(auto_now=True)
            day = models.IntegerField(choices=Day.choices)
            location = models.CharField(max_length=128, blank=True)
            observation = models.TextField(null=True, blank=True)
            parish = models.ForeignKey(
                Parish, on_delete=models.CASCADE, related_name="schedules"
            )
            source = models.ForeignKey(Source, on_delete=models.RESTRICT, blank=True, null=True)
            start_time = models.TimeField()
            end_time = models.TimeField(null=True, blank=True)
            type = models.CharField(choices=Type.choices, default=Type.MASS)
            verified_at = models.DateField(blank=True, null=True)

            class Meta:
                unique_together = ("parish", "day", "start_time")
        ```

        Your output will be used to create multiple Schedules.
        ```python
        for schedule_data in json.loads(ai_response)['schedules']:
            schedules = Schedule(parish=parish, source=source, **schedule_data)

        Schedule.objects.delete(parish=parish)
        Schedule.objects.bulk_create(schedules)
        ```

        An example:
        Messages:
        ```
        [Message at 2024-09-16]
        Bom dia. Qual o horário das missas na paróquia?
        [Message at 2024-09-16]
        Hoje as 19h
        [Message at 2024-09-16]
        E nos outros dias?
        [Message at 2024-09-16]
        De terça à sábado às 17h30  e  aos domingos às 9h e 19h
        [Message at 2024-09-16]
        Prineira quinta do mês missa por cura é liberação
        [Message at 2024-09-16]
        Primeira sexta feira missa só sagrado coração de Jesus
        [Message at 2024-09-16]
        Certo. Obrigado
        [Message at 2024-09-16]
        E vocês atendem confissão? Se sim, que dias e horários?
        [Message at 2024-09-16]
        terça, quarta e quinta a partir das 16h

        [Message at 2024-09-16]
        Obrigado!
        ```
        AI response:
        ```json
        {
            "schedules": [
                {
                    "day": 2,
                    "location": "",
                    "observation": null,
                    "start_time": "17:30",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 3,
                    "location": "",
                    "observation": null,
                    "start_time": "17:30",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 4,
                    "location": "",
                    "observation": "Missa de Cura e Libertação na primeira quinta-feira do mês",
                    "start_time": "17:30",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 5,
                    "location": "",
                    "observation": "Missa do Sagrado Coração de Jesus na primeira sexta-feira do mês",
                    "start_time": "17:30",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 6,
                    "location": "",
                    "observation": null,
                    "start_time": "17:30",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 0,
                    "location": "",
                    "observation": null,
                    "start_time": "09:00",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 0,
                    "location": "",
                    "observation": null,
                    "start_time": "19:00",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 2,
                    "location": "",
                    "observation": null,
                    "start_time": "16:00",
                    "end_time": null,
                    "type": "confession",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 3,
                    "location": "",
                    "observation": null,
                    "start_time": "16:00",
                    "end_time": null,
                    "type": "confession",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 4,
                    "location": "",
                    "observation": null,
                    "start_time": "18:00",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                }
            ]
        }
        ```"""
    ),
    json_object=True,
)
AI_RESPONSE = """\
{
    "schedules": [
        {
            "day": 1,
            "location": "",
            "observation": null,
            "start_time": "06:00",
            "end_time": null,
            "type": "mass",
            "verified_at": "2024-09-16"
        },
        {
            "day": 3,
            "location": "",
            "observation": null,
            "start_time": "06:00",
            "end_time": null,
            "type": "mass",
            "verified_at": "2024-09-16"
        },
        {
            "day": 5,
            "location": "",
            "observation": null,
            "start_time": "06:00",
            "end_time": null,
            "type": "mass",
            "verified_at": "2024-09-16"
        },
        {
            "day": 6,
            "location": "",
            "observation": null,
            "start_time": "06:00",
            "end_time": null,
            "type": "mass",
            "verified_at": "2024-09-16"
        },
        {
            "day": 2,
            "location": "",
            "observation": null,
            "start_time": "19:30",
            "end_time": null,
            "type": "mass",
            "verified_at": "2024-09-16"
        },
        {
            "day": 3,
            "location": "",
            "observation": "Celebração especial às 19:30",
            "start_time": "19:30",
            "end_time": null,
            "type": "mass",
            "verified_at": "2024-09-16"
        },
        {
            "day": 6,
            "location": "",
            "observation": null,
            "start_time": "19:30",
            "end_time": null,
            "type": "mass",
            "verified_at": "2024-09-16"
        },
        {
            "day": 0,
            "location": "",
            "observation": null,
            "start_time": "07:00",
            "end_time": null,
            "type": "mass",
            "verified_at": "2024-09-16"
        },
        {
            "day": 0,
            "location": "",
            "observation": null,
            "start_time": "09:00",
            "end_time": null,
            "type": "mass",
            "verified_at": "2024-09-16"
        },
        {
            "day": 0,
            "location": "",
            "observation": null,
            "start_time": "18:00",
            "end_time": null,
            "type": "mass",
            "verified_at": "2024-09-16"
        },
        {
            "day": 4,
            "location": "",
            "observation": "Adoração e benção do Santíssimo às 18:00",
            "start_time": "15:00",
            "end_time": "18:00",
            "type": "adoration",
            "verified_at": "2024-09-16"
        }
    ]
}
"""


# class ai_response:
#     @staticmethod
#     def text():
#         return AI_RESPONSE


data = json.loads(ai_response.text())

to_be_created = []
for s in data["schedules"]:
    start_time = parse_time(s.pop("start_time"))

    if end_time := s.pop("end_time", None):
        end_time = parse_time(end_time)

    to_be_created.append(
        Schedule(
            parish=parish,
            source=source,
            **s,
            start_time=start_time,
            end_time=end_time,
        )
    )


def model_to_dicts(os):
    return [model_to_dict(s, exclude=("id",)) for s in os]


def compare(ss1, ss2):
    l1 = sorted(model_to_dicts(ss1), key=lambda x: (x["day"], x["start_time"]))
    l2 = sorted(model_to_dicts(ss2), key=lambda x: (x["day"], x["start_time"]))
    print(diff(l1, l2))


to_be_deleted = Schedule.objects.filter(parish=parish)

# to_be_created = sorted(to_be_created, key=lambda x: (x.day, x.start_time))
# to_be_deleted = sorted(to_be_deleted, key=lambda x: (x.day, x.start_time))

print("=" * 150)

print(MESSAGE)

print("-" * 100)

print("TO BE CREATED")
for s in to_be_created:
    print(s.type, s, s.observation or "")

print("-" * 100)

print("TO BE DELETED")
for s in to_be_deleted:
    print(s.type, s, s.observation or "")

print("-" * 100)

print("COMPARE")
compare(to_be_deleted, to_be_created)

print("=" * 150)


def ynput():
    while True:
        yn = input("Approve? (Y/n) ")
        if yn == "Y":
            return True
        elif yn == "n":
            return False


for s in to_be_deleted:
    print("DELETE?", s.type, s, s.observation or "")
    if ynput():
        s.delete()


for s in to_be_created:
    print("SAVE?", s.type, s, s.observation or "")
    if ynput():
        s.save()
