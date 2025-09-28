# Migration to create database cache table

from django.core.management.commands.createcachetable import Command
from django.db import migrations


def create_cache_table(apps, schema_editor):
    """Create cache table using Django's createcachetable command"""
    command = Command()
    sql = command.sql_create_cache_table("missas_cache_table")
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(sql)


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
