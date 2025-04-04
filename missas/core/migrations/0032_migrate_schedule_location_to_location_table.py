# Generated by Django 5.1.6 on 2025-03-03 21:17

from django.db import migrations
from django.utils.text import slugify


def forwards(apps, schema_editor):
    Schedule = apps.get_model("core", "Schedule")
    Location = apps.get_model("core", "Location")

    for s in Schedule.objects.all():
        location, _ = Location.objects.get_or_create(
            city=s.parish.city,
            name=s.location,
            slug=slugify(" ".join((s.parish.slug, s.location))),
            parish=s.parish,
        )
        location.schedules.add(s)


def backwards(apps, schema_editor):
    Location = apps.get_model("core", "Location")
    Location.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0031_location_schedule_location"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
