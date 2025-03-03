# Generated by Django 5.1.6 on 2025-04-04 12:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0028_contactrequest"),
    ]

    operations = [
        migrations.CreateModel(
            name="Location",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(blank=True, max_length=128)),
                ("slug", models.SlugField(blank=True, max_length=128)),
                (
                    "city",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="locations",
                        to="core.city",
                    ),
                ),
                (
                    "parish",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="locations",
                        to="core.parish",
                    ),
                ),
                (
                    "schedules",
                    models.ManyToManyField(
                        related_name="locations", to="core.schedule"
                    ),
                ),
            ],
            options={
                "unique_together": {("slug", "city")},
            },
        ),
    ]
