"""
Management command to migrate data between databases.

This command exports all data from the current database and can import it into another database.
Useful for migrating from PostgreSQL to SQLite or vice versa.

Usage:
    # Export data to JSON file
    python manage.py migrate_db export data.json

    # Import data from JSON file (run after changing DATABASE_URL)
    python manage.py migrate_db import data.json
"""

import json

from django.core.management.base import BaseCommand
from django.core.serializers import deserialize, serialize

from missas.core.models import (
    City,
    Contact,
    ContactRequest,
    Location,
    Parish,
    Schedule,
    Source,
    State,
)


class Command(BaseCommand):
    help = "Migrate data between databases"

    # Order matters: models with dependencies must come after their dependencies
    MODELS = [State, City, Source, Parish, Contact, Location, Schedule, ContactRequest]

    def add_arguments(self, parser):
        parser.add_argument(
            "action", choices=["export", "import"], help="Action to perform"
        )
        parser.add_argument("file", help="JSON file to export to or import from")

    def handle(self, *args, **options):
        action = options["action"]
        filename = options["file"]

        if action == "export":
            self.export_data(filename)
        else:
            self.import_data(filename)

    def export_data(self, filename):
        self.stdout.write("Exporting data...")

        data = []
        for model in self.MODELS:
            objects = model.objects.all()
            count = objects.count()
            self.stdout.write(f"  Exporting {count} {model.__name__} objects...")
            serialized = serialize("json", objects)
            data.extend(json.loads(serialized))

        with open(filename, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stdout.write(
            self.style.SUCCESS(f"✓ Successfully exported data to {filename}")
        )

    def import_data(self, filename):
        self.stdout.write("Importing data...")

        with open(filename) as f:
            data = json.load(f)

        # Group by model to maintain order
        model_data = {}
        for obj in data:
            model = obj["model"]
            if model not in model_data:
                model_data[model] = []
            model_data[model].append(obj)

        # Import in correct order
        for model in self.MODELS:
            model_name = f"{model._meta.app_label}.{model._meta.model_name}"
            if model_name in model_data:
                objects = model_data[model_name]
                self.stdout.write(
                    f"  Importing {len(objects)} {model.__name__} objects..."
                )
                for obj in deserialize("json", json.dumps(objects)):
                    obj.save()

        self.stdout.write(
            self.style.SUCCESS(f"✓ Successfully imported data from {filename}")
        )
