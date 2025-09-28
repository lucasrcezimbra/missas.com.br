# Migration to create database cache table

import sys
from io import StringIO

from django.core.management import call_command
from django.db import migrations


def create_cache_table(apps, schema_editor):
    """Create cache table using Django's createcachetable command"""
    # Capture output to prevent it from being printed
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        call_command('createcachetable', 'missas_cache_table', verbosity=0)
    finally:
        sys.stdout = old_stdout


def delete_cache_table(apps, schema_editor):
    """Drop cache table"""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS missas_cache_table;")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0028_contactrequest"),
    ]

    operations = [
        migrations.RunPython(
            create_cache_table,
            reverse_code=delete_cache_table,
        ),
    ]
