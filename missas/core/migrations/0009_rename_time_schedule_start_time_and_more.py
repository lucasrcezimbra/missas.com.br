# Generated by Django 5.0 on 2023-12-21 11:04

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_alter_schedule_unique_together"),
    ]

    operations = [
        migrations.RenameField(
            model_name="schedule",
            old_name="time",
            new_name="start_time",
        ),
        migrations.AlterUniqueTogether(
            name="schedule",
            unique_together={("parish", "day", "start_time")},
        ),
    ]
