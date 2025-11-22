import json
import os
import re
import sys
from datetime import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Contact, Parish, Schedule, Source, State  # noqa


DAY_MAPPING = {
    "Domingo": Schedule.Day.SUNDAY,
    "Segunda": Schedule.Day.MONDAY,
    "Terça": Schedule.Day.TUESDAY,
    "Quarta": Schedule.Day.WEDNESDAY,
    "Quinta": Schedule.Day.THURSDAY,
    "Sexta": Schedule.Day.FRIDAY,
    "Sábado": Schedule.Day.SATURDAY,
}


def extract_field(text, field_name):
    pattern = rf"{field_name}:\n([^\n]+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def extract_city_name(text):
    city = extract_field(text, "Cidade")
    if city:
        city = city.replace("-CE", "").replace(" (CE)", "").replace("–", "").strip()
    return city


def parse_time(time_str):
    time_str = time_str.strip().replace("h", ":")
    if ":" not in time_str:
        time_str = time_str + ":00"

    parts = time_str.split(":")
    if len(parts) == 2:
        hour, minute = parts
        try:
            return time(int(hour), int(minute))
        except (ValueError, TypeError):
            return None
    return None


def parse_schedules(schedule_text):
    schedules = []

    mass_schedule_match = re.search(
        r"Horário de Missa na Matriz(.+?)Horário de Atendimento",
        schedule_text,
        re.DOTALL,
    )

    if not mass_schedule_match:
        return schedules

    mass_section = mass_schedule_match.group(1)

    for day_pt, day_enum in DAY_MAPPING.items():
        pattern = rf"{day_pt}:\n([^\n]+)"
        match = re.search(pattern, mass_section)

        if match:
            times_str = match.group(1).strip()
            if not times_str or times_str == "—":
                continue

            time_parts = re.split(r"\s*\|\s*", times_str)

            for time_str in time_parts:
                time_str = time_str.strip()
                if not time_str:
                    continue

                parsed_time = parse_time(time_str)
                if parsed_time:
                    schedules.append({"day": day_enum, "time": parsed_time})

    return schedules


with open("./contrib/fortaleza.jsonl") as f:
    datas = [json.loads(line) for line in f.readlines()]

state, _ = State.objects.get_or_create(
    short_name="CE", defaults={"name": "Ceará", "slug": "ceara"}
)

source, _ = Source.objects.get_or_create(
    link="https://www.arquidiocesedefortaleza.org.br/",
    defaults={
        "description": "Site da Arquidiocese de Fortaleza",
        "type": Source.Type.SITE,
    },
)

for d in datas:
    schedule_text = d.get("schedule_text", "")
    if not schedule_text:
        print(f"Skipping {d['parish_name']} - no schedule text")
        continue

    city_name = extract_city_name(schedule_text)
    if not city_name:
        print(f"Skipping {d['parish_name']} - no city found")
        continue

    try:
        city, created = City.objects.get_or_create(
            slug=slugify(city_name),
            state=state,
            defaults={"name": city_name},
        )
        if created:
            print(f"Created city: {city}")
    except Exception as e:
        print(f"Error creating city {city_name}: {e}")
        continue

    parish_name = d["parish_name"]
    try:
        parish, created = Parish.objects.get_or_create(
            slug=slugify(parish_name),
            city=city,
            defaults={"name": parish_name},
        )
        if created:
            print(f"Created parish: {parish}")
    except Exception as e:
        print(f"Error creating parish {parish_name}: {e}")
        continue

    email = extract_field(schedule_text, "Email")
    email = email.replace("[email protected]", "").strip()

    phone = extract_field(schedule_text, "Fixo")
    phone2 = extract_field(schedule_text, "Celular")
    whatsapp = extract_field(schedule_text, "WhatsApp")
    facebook = extract_field(schedule_text, "Facebook")
    instagram = extract_field(schedule_text, "Instagram")

    try:
        contact, created = Contact.objects.update_or_create(
            parish=parish,
            defaults={
                "email": email[:254] if email else "",
                "phone": phone[:16] if phone else "",
                "phone2": phone2[:16] if phone2 else "",
                "whatsapp": whatsapp[:16] if whatsapp else "",
                "facebook": facebook[:256] if facebook else "",
                "instagram": instagram[:64] if instagram else "",
            },
        )
        if created:
            print(f"Created contact for {parish}")
    except Exception as e:
        print(f"Error creating contact for {parish}: {e}")

    schedules = parse_schedules(schedule_text)
    for sched in schedules:
        try:
            schedule_obj, created = Schedule.objects.get_or_create(
                parish=parish,
                day=sched["day"],
                start_time=sched["time"],
                defaults={
                    "type": Schedule.Type.MASS,
                    "source": source,
                },
            )
            if created:
                print(f"Created schedule: {schedule_obj}")
        except IntegrityError:
            pass
        except Exception as e:
            print(f"Error creating schedule for {parish}: {e}")

print("\nImport completed!")
