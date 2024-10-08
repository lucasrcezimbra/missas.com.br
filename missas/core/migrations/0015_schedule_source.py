# Generated by Django 5.0.4 on 2024-08-28 12:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_default_source"),
    ]

    operations = [
        migrations.AddField(
            model_name="schedule",
            name="source",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.RESTRICT,
                to="core.source",
            ),
        ),
    ]
