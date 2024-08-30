# Generated by Django 5.1 on 2024-08-30 09:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0017_city_created_at_city_updated_at_parish_created_at_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="city",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="parish",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="schedule",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="source",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="state",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
