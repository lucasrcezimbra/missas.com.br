# Generated by Django 5.1 on 2024-08-30 09:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0018_alter_city_created_at_alter_parish_created_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="schedule",
            name="verified_at",
            field=models.DateField(blank=True, null=True),
        ),
    ]