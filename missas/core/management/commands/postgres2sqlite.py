import datetime

from django.core.management.base import BaseCommand
from django.db import connections, transaction


class Command(BaseCommand):
    help = "Copy all data from PostgreSQL (default) to SQLite (new) database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be copied without actually copying",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Skip confirmation prompt",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        no_input = options["no_input"]

        source_db = "old"
        target_db = "default"

        self.stdout.write(
            self.style.WARNING(
                f"\nThis will copy all data from '{source_db}' (PostgreSQL) "
                f"to '{target_db}' (SQLite)"
            )
        )

        if not dry_run and not no_input:
            confirm = input(
                f"\nThis will DELETE all existing data in '{target_db}' database. "
                "Are you sure? [yes/N]: "
            )
            if confirm.lower() != "yes":
                self.stdout.write(self.style.ERROR("\nOperation cancelled."))
                return

        tables = self.get_all_tables(source_db)

        tables_to_skip = {"django_cache"}
        tables = [t for t in tables if t not in tables_to_skip]

        self.stdout.write(self.style.SUCCESS(f"\nFound {len(tables)} tables to copy"))

        if tables_to_skip:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipping tables: {', '.join(sorted(tables_to_skip))}"
                )
            )

        ordered_tables = self.order_tables_by_dependencies(tables, source_db)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n--- DRY RUN MODE (no changes will be made) ---")
            )

        self.stdout.write("\nCopy order based on dependencies:")
        for i, table in enumerate(ordered_tables, 1):
            count = self.get_table_count(table, source_db)
            self.stdout.write(f"  {i}. {table} ({count} rows)")

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS("\nDry run complete. No data was copied.")
            )
            return

        self.copy_all_tables(ordered_tables, source_db, target_db)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Successfully copied all data from '{source_db}' to '{target_db}'"
            )
        )

    def get_all_tables(self, db_alias):
        """Get list of all tables in the database."""
        with connections[db_alias].cursor() as cursor:
            return connections[db_alias].introspection.table_names(cursor)

    def get_table_count(self, table_name, db_alias):
        """Get row count for a table."""
        with connections[db_alias].cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
            return cursor.fetchone()[0]

    def get_foreign_keys(self, table_name, db_alias):
        """Get foreign key relationships for a table."""
        with connections[db_alias].cursor() as cursor:
            relations = connections[db_alias].introspection.get_relations(
                cursor, table_name
            )
            return relations

    def order_tables_by_dependencies(self, tables, db_alias):
        """
        Order tables based on foreign key dependencies using topological sort.
        Tables with no dependencies come first.
        """
        dependencies = {}
        all_tables = set(tables)

        for table in tables:
            fk_relations = self.get_foreign_keys(table, db_alias)
            deps = set()
            for column_index, (ref_table, ref_column) in fk_relations.items():
                if ref_table in all_tables and ref_table != table:
                    deps.add(ref_table)
            dependencies[table] = deps

        ordered = []
        visited = set()
        visiting = set()

        def visit(table):
            if table in visited:
                return
            if table in visiting:
                return

            visiting.add(table)

            for dep in dependencies.get(table, set()):
                if dep in dependencies:
                    visit(dep)

            visiting.remove(table)
            visited.add(table)
            ordered.append(table)

        for table in tables:
            visit(table)

        return ordered

    def copy_all_tables(self, tables, source_db, target_db):
        """Copy all tables from source to target database."""
        try:
            with transaction.atomic(using=target_db):
                self.clear_target_database(tables, target_db)

                for table in tables:
                    self.copy_table(table, source_db, target_db)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"\n✗ Error during copy: {e}\n" "All changes have been rolled back."
                )
            )
            raise

    def convert_value_for_sqlite(self, value):
        """Convert PostgreSQL values to SQLite-compatible format."""
        if isinstance(value, datetime.time):
            return value.isoformat()
        elif isinstance(value, datetime.date):
            return value.isoformat()
        elif isinstance(value, datetime.datetime):
            return value.isoformat()
        return value

    def clear_target_database(self, tables, target_db):
        """Clear all data from target database tables."""
        self.stdout.write("\nClearing target database...")

        reversed_tables = list(reversed(tables))

        with connections[target_db].cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF")

            for table in reversed_tables:
                cursor.execute(f"DELETE FROM {table}")  # noqa: S608

            cursor.execute("PRAGMA foreign_keys = ON")

        self.stdout.write(self.style.SUCCESS("✓ Target database cleared"))

    def copy_table(self, table_name, source_db, target_db):
        """Copy all data from one table to another."""
        count = self.get_table_count(table_name, source_db)

        if count == 0:
            self.stdout.write(f"  Skipping {table_name} (0 rows)")
            return

        self.stdout.write(f"  Copying {table_name} ({count} rows)...", ending="")

        with connections[source_db].cursor() as source_cursor:
            source_cursor.execute(f"SELECT * FROM {table_name}")  # noqa: S608
            columns = [col[0] for col in source_cursor.description]
            rows = source_cursor.fetchall()

        if not rows:
            self.stdout.write(self.style.SUCCESS(" ✓"))
            return

        column_names = ", ".join(columns)
        placeholders = ", ".join(["?" for _ in columns])
        insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"  # noqa: S608

        converted_rows = [
            tuple(self.convert_value_for_sqlite(val) for val in row) for row in rows
        ]

        with connections[target_db].cursor() as target_cursor:
            target_cursor.execute("PRAGMA foreign_keys = OFF")
            raw_cursor = target_cursor.cursor
            raw_cursor.executemany(insert_sql, converted_rows)
            target_cursor.execute("PRAGMA foreign_keys = ON")

        self.stdout.write(self.style.SUCCESS(" ✓"))
