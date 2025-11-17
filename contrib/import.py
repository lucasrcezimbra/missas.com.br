import json
import os
import sys
from datetime import datetime
from textwrap import dedent

import django
import llm
from decouple import config
from django.utils.dateparse import parse_time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import Contact, City, Parish, Schedule, Source  # noqa


"""
// JS snippet to extract message from WhatsApp Web
// 1. Open WhatsApp web
// 2. Open the conversation to extract the messages
// 3. Open Browser Inspect > Console
// 4. Run this code:
var messages = []
document.querySelectorAll('#main .copyable-text').forEach(element => {
    if (element.tagName.toLowerCase() === 'div') {
        messages.push(element.getAttribute('data-pre-plain-text'));
        messages.push(element.innerText);
    }
});
console.log(document.getElementById('main').querySelector('header').innerText.replaceAll(' ', '').replace('-', ''));
console.log(messages.join('\n'))
"""


phone = sys.argv[1]
messages = sys.argv[2]

try:
    contact = Contact.objects.get(whatsapp=phone)
    print(f"{contact=}")
except Contact.DoesNotExist:
    phone = phone[:5] + "9" + phone[5:]
    contact = Contact.objects.get(whatsapp=phone)
    print(f"{contact=}")


parish = contact.parish
print(f"{parish=}")
if not parish:
    raise Exception("No parish")

source = Source.objects.get(
    type=Source.Type.WHATSAPP, description="WhatsApp da Paróquia"
)
print(f"{source=}")

model = llm.get_model("o3-mini")
model.key = config("OPENAI_API_KEY")

ai_response = model.prompt(
    messages,
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
                OTHER = ("other", "Outro")

            created_at = models.DateTimeField(auto_now_add=True)
            updated_at = models.DateTimeField(auto_now=True)
            day = models.IntegerField(choices=Day.choices)
            location_name = models.CharField(max_length=128, blank=True)
            observation = models.TextField(null=True, blank=True)
            parish = models.ForeignKey(
                Parish, on_delete=models.CASCADE, related_name="schedules"
            )
            source = models.ForeignKey(Source, on_delete=models.RESTRICT, blank=True, null=True)
            start_time = models.TimeField()
            end_time = models.TimeField(null=True, blank=True)
            type = models.CharField(choices=Type.choices, default=Type.MASS)
            other_type_description = models.CharField(
                max_length=100,
                blank=True,
                help_text="Tipo de celebração quando 'Outro' for selecionado",
            )
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
        [12:28, 16/09/2024] Missas.com.br:
        Bom dia. Qual o horário das missas na paróquia?
        [12:29, 16/09/2024] +55 84 9876-5432:
        Hoje as 19h
        [12:29, 16/09/2024] Missas.com.br:
        E nos outros dias?
        [12:30, 16/09/2024] +55 84 9876-5432:
        De terça à sábado às 17h30  e  aos domingos às 9h e 19h
        [12:30, 16/09/2024] +55 84 9876-5432:
        Prineira quinta do mês missa por cura é liberação
        [12:30, 16/09/2024] +55 84 9876-5432:
        Primeira sexta feira missa só sagrado coração de Jesus
        [12:31, 16/09/2024] Missas.com.br:
        Certo. Obrigado
        [12:31, 16/09/2024] Missas.com.br:
        E vocês atendem confissão? Se sim, que dias e horários?
        [12:32, 16/09/2024] +55 84 9876-5432:
        terça, quarta e quinta a partir das 16h
        [12:32, 16/09/2024] Missas.com.br:
        Obrigado!
        ```
        AI response:
        ```json
        {
            "schedules": [
                {
                    "day": 2,
                    "location_name": "",
                    "observation": "",
                    "start_time": "17:30",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 3,
                    "location_name": "",
                    "observation": "",
                    "start_time": "17:30",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 4,
                    "location_name": "",
                    "observation": "Missa de Cura e Libertação na primeira quinta-feira do mês",
                    "start_time": "17:30",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 5,
                    "location_name": "",
                    "observation": "Missa do Sagrado Coração de Jesus na primeira sexta-feira do mês",
                    "start_time": "17:30",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 6,
                    "location_name": "",
                    "observation": "",
                    "start_time": "17:30",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 0,
                    "location_name": "",
                    "observation": "",
                    "start_time": "09:00",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 0,
                    "location_name": "",
                    "observation": "",
                    "start_time": "19:00",
                    "end_time": null,
                    "type": "mass",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 2,
                    "location_name": "",
                    "observation": "",
                    "start_time": "16:00",
                    "end_time": null,
                    "type": "confession",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 3,
                    "location_name": "",
                    "observation": "",
                    "start_time": "16:00",
                    "end_time": null,
                    "type": "confession",
                    "verified_at": "2024-09-16"
                },
                {
                    "day": 4,
                    "location_name": "",
                    "observation": "",
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

data = json.loads(ai_response.text())

schedules = []

for s in data["schedules"]:
    start_time = parse_time(s.pop("start_time"))

    if end_time := s.pop("end_time", None):
        end_time = parse_time(end_time)

    try:
        schedule = Schedule.objects.get(
            parish=parish, day=s["day"], type=s["type"], start_time=start_time
        )
    except Schedule.DoesNotExist:
        schedule = Schedule(
            parish=parish, day=s["day"], type=s["type"], start_time=start_time
        )

    schedule.end_time = end_time

    if s["location_name"].lower() != schedule.location_name.lower():
        schedule.location_name = s["location_name"]

    if s["observation"].lower() != schedule.observation.lower():
        schedule.observation = s["observation"]

    schedule.source = source
    schedule.verified_at = datetime.strptime(s["verified_at"], "%Y-%m-%d").date()

    schedules.append(schedule)


to_be_deleted = [
    s for s in Schedule.objects.filter(parish=parish) if s not in schedules
]


def ynput():
    while True:
        yn = input("Approve? (Y/n) ")
        if yn == "Y":
            return True
        elif yn == "n":
            return False


print("=" * 150)

print(messages)

print("=" * 150)

for s in to_be_deleted:
    print("DELETE?", s.type, s, s.observation or "", s.tracker.changed())

    if ynput():
        s.delete()

    print("-" * 100)

print("=" * 150)

for s in schedules:
    if not s.tracker.changed():
        print("Didn't change", s.type, s, s.observation or "", s.tracker.changed())
        print("-" * 100)
        continue

    if s.pk:
        message = "UPDATE?"
    else:
        message = "CREATE?"

    print(message, s.type, s, s.observation or "", s.tracker.changed())

    if ynput():
        s.save()

    print("-" * 100)

print("=" * 150)
