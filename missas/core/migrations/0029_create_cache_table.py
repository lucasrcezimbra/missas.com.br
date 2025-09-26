# Generated manually for database cache backend

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0028_contactrequest"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE django_cache (
                cache_key VARCHAR(255) NOT NULL PRIMARY KEY,
                value BYTEA NOT NULL,
                expires TIMESTAMP WITH TIME ZONE NOT NULL
            );
            CREATE INDEX django_cache_expires ON django_cache (expires);
            """,
            reverse_sql="DROP TABLE django_cache;",
        ),
    ]
