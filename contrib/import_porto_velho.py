import json
import os
import sys
from datetime import datetime
from textwrap import dedent

import django
import llm
from decouple import config
from django.utils.dateparse import parse_time
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import City, Parish, Schedule, Source, State  # noqa


def parse_schedules_with_llm(parish_name, times_list):
    """Use LLM to parse unstructured schedule text into structured data."""
    model = llm.get_model("gpt-4o")
    model.key = config("OPENAI_API_KEY")

    times_text = "\n".join(times_list)

    ai_response = model.prompt(
        times_text,
        system=dedent(
            f"""\
            You are a Django management tool. You help parse unstructured mass schedule text into structured data.

            Parish: {parish_name}

            This is the Django model:

            ```python
            class Schedule(models.Model):
                class Day(models.IntegerChoices):
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

                day = models.IntegerField(choices=Day.choices)
                location_name = models.CharField(max_length=128, blank=True)
                observation = models.TextField(blank=True)
                start_time = models.TimeField()
                end_time = models.TimeField(null=True, blank=True)
                type = models.CharField(choices=Type.choices, default=Type.MASS)
                verified_at = models.DateField(blank=True, null=True)
            ```

            Parse the provided text and extract all mass schedules. Look for:
            - Day references (Domingo, Segunda, Terça, Quarta, Quinta, Sexta, Sábado)
            - Time patterns (8h, 19h30, 7h30, etc.)
            - Ranges like "Segunda a Sexta" or "Segunda à Sexta-feira"
            - Special masses (first Friday, first Thursday, etc.) should go in observation

            Return ONLY valid mass schedules. Ignore:
            - Office hours (horário de atendimento, secretaria)
            - Historical information
            - Contact information
            - Dates like "Porto Velho, terça, 18 de novembro de 2025"

            Output format:
            ```json
            {{
                "schedules": [
                    {{
                        "day": 0,
                        "location_name": "",
                        "observation": "",
                        "start_time": "08:00",
                        "end_time": null,
                        "type": "mass",
                        "verified_at": "2025-11-22"
                    }}
                ]
            }}
            ```

            If no valid schedules are found, return: {{"schedules": []}}
            """
        ),
        json_object=True,
    )

    return json.loads(ai_response.text())


def get_or_create_state():
    """Get or create Rondônia state."""
    state, created = State.objects.get_or_create(
        short_name="RO",
        defaults={
            "name": "Rondônia",
            "slug": "rondonia",
        },
    )
    if created:
        print(f"✓ Created state: {state}")
    return state


def get_or_create_source():
    """Get or create source for Porto Velho scraper."""
    source, created = Source.objects.get_or_create(
        type=Source.Type.SITE,
        description="Site da Arquidiocese de Porto Velho",
        defaults={
            "link": "https://arquidiocesedeportovelho.org.br/paroquias/",
        },
    )
    if created:
        print(f"✓ Created source: {source}")
    return source


def extract_city_from_parish_name(parish_name):
    """
    Try to extract city name from parish name.
    Returns tuple of (cleaned_parish_name, city_name or None)
    """
    # Common patterns to look for city names
    # E.g., "Paróquia São José – Monte Negro"
    # E.g., "Paróquia Nossa Senhora Aparecida – Distrito de São Carlos"

    if "–" in parish_name:
        parts = parish_name.split("–")
        if len(parts) == 2:
            name_part = parts[0].strip()
            location_part = parts[1].strip()

            # Remove common prefixes
            location_part = location_part.replace("Distrito de", "").strip()

            return name_part, location_part

    # Default to Porto Velho if no city is found
    return parish_name, "Porto Velho"


def get_or_create_city(state, city_name):
    """Get or create city in the given state."""
    city_slug = slugify(city_name)
    city, created = City.objects.get_or_create(
        slug=city_slug,
        state=state,
        defaults={
            "name": city_name,
        },
    )
    if created:
        print(f"✓ Created city: {city}")
    return city


def get_or_create_parish(city, parish_name):
    """Get or create parish in the given city."""
    parish_slug = slugify(parish_name)
    parish, created = Parish.objects.get_or_create(
        slug=parish_slug,
        city=city,
        defaults={
            "name": parish_name,
        },
    )
    if created:
        print(f"✓ Created parish: {parish}")
    return parish


def process_schedules(parish, source, schedules_data):
    """Process and save schedules for a parish."""
    schedules_to_save = []

    for s in schedules_data:
        start_time = parse_time(s["start_time"])
        if not start_time:
            print(f"  ⚠ Invalid start time: {s['start_time']}")
            continue

        end_time = None
        if s.get("end_time"):
            end_time = parse_time(s["end_time"])

        verified_at = None
        if s.get("verified_at"):
            try:
                verified_at = datetime.strptime(s["verified_at"], "%Y-%m-%d").date()
            except ValueError:
                pass

        # Try to get existing schedule
        try:
            schedule = Schedule.objects.get(
                parish=parish,
                day=s["day"],
                start_time=start_time,
            )
            action = "UPDATE"
        except Schedule.DoesNotExist:
            schedule = Schedule(
                parish=parish,
                day=s["day"],
                start_time=start_time,
            )
            action = "CREATE"

        # Update fields
        schedule.end_time = end_time
        schedule.location_name = s.get("location_name", "")
        schedule.observation = s.get("observation", "")
        schedule.type = s.get("type", "mass")
        schedule.source = source
        schedule.verified_at = verified_at

        schedules_to_save.append((schedule, action))

    return schedules_to_save


def confirm_action(message, item):
    """Ask user to confirm an action."""
    while True:
        print(f"\n{message}")
        print(f"  {item}")
        response = input("  Proceed? (Y/n/s=skip all): ").strip()
        if response == "Y":
            return True
        elif response == "n":
            return False
        elif response == "s":
            return "skip_all"


def main():
    jsonl_file = sys.argv[1] if len(sys.argv) > 1 else "porto_velho.jsonl"

    print(f"Reading {jsonl_file}...")

    state = get_or_create_state()
    source = get_or_create_source()

    with open(jsonl_file, "r", encoding="utf-8") as f:
        entries = [json.loads(line) for line in f]

    print(f"\n✓ Found {len(entries)} parishes in {jsonl_file}\n")
    print("=" * 100)

    skip_all = False

    for i, entry in enumerate(entries, 1):
        parish_name = entry["parish_name"]
        times = entry["times"]

        print(f"\n[{i}/{len(entries)}] Processing: {parish_name}")
        print(f"  Raw times data ({len(times)} lines)")

        # Extract city from parish name
        clean_parish_name, city_name = extract_city_from_parish_name(parish_name)

        # Get or create city and parish
        city = get_or_create_city(state, city_name)
        parish = get_or_create_parish(city, clean_parish_name)

        # Parse schedules with LLM
        print(f"  🤖 Parsing schedules with LLM...")
        try:
            parsed_data = parse_schedules_with_llm(parish_name, times)
            schedules_data = parsed_data.get("schedules", [])

            if not schedules_data:
                print(f"  ⚠ No schedules found for {parish_name}")
                continue

            print(f"  ✓ Found {len(schedules_data)} schedules")

            # Process schedules
            schedules_to_save = process_schedules(parish, source, schedules_data)

            # Confirm and save
            if not skip_all:
                print(f"\n  Schedules to save:")
                for schedule, action in schedules_to_save:
                    print(f"    {action}: {schedule}")

                result = confirm_action(f"  Save {len(schedules_to_save)} schedules?", parish)
                if result == "skip_all":
                    skip_all = True
                elif result:
                    for schedule, action in schedules_to_save:
                        schedule.save()
                        print(f"    ✓ {action}: {schedule}")
            else:
                # Skip all mode - just save without confirmation
                for schedule, action in schedules_to_save:
                    schedule.save()
                    print(f"    ✓ {action}: {schedule}")

        except Exception as e:
            print(f"  ✗ Error processing {parish_name}: {e}")
            import traceback
            traceback.print_exc()
            continue

        print("-" * 100)

    print("\n" + "=" * 100)
    print("✓ Import complete!")


if __name__ == "__main__":
    main()
