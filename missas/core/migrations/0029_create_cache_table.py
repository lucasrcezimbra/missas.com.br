from django.core.management import call_command
from django.db import migrations


def create_cache_table(apps, schema_editor):
    call_command("createcachetable", "django_cache")


def drop_cache_table(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('DROP TABLE IF EXISTS "django_cache"')


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0028_contactrequest"),
    ]

    operations = [
        migrations.RunPython(
            create_cache_table,
            reverse_code=drop_cache_table,
        ),
    ]
