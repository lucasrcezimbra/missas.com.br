# Migration to create database cache table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0028_contactrequest"),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE TABLE missas_cache_table (
                cache_key VARCHAR(255) NOT NULL PRIMARY KEY,
                value TEXT NOT NULL,
                expires TIMESTAMP NOT NULL
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS missas_cache_table;",
        ),
        migrations.RunSQL(
            "CREATE INDEX missas_cache_table_expires ON missas_cache_table (expires);",
            reverse_sql="DROP INDEX IF EXISTS missas_cache_table_expires;",
        ),
    ]
