from django.db import migrations


def copy_data_postgres_to_sqlite(apps, schema_editor):
    """Copy all data from PostgreSQL (default) to SQLite (new)"""

    # Skip during tests - this migration is only for production data migration
    db_name = schema_editor.connection.settings_dict.get("NAME", "")
    if "test" in db_name.lower():
        print("\n⊗ Skipping data migration during test run\n")
        return

    # Get database aliases
    source_db = "default"  # PostgreSQL
    target_db = "new"  # SQLite
    current_db = schema_editor.connection.alias

    # Skip if running on the target database (we only want to create schema there)
    # The data copy should only happen when running on the source database
    if current_db == target_db:
        print(
            f"\n⊗ Skipping data migration when running on target database '{target_db}'\n"
        )
        print("   This migration only copies data when run on the source database.\n")
        return

    # Only proceed if running on the source database
    if current_db != source_db:
        print(f"\n⊗ Skipping data migration on database '{current_db}'\n")
        print(
            f"   This migration only runs on '{source_db}' to copy data to '{target_db}'.\n"
        )
        return

    # Models to copy in dependency order
    models_to_copy = [
        # Django built-in apps
        ("contenttypes", "ContentType"),
        ("auth", "Permission"),
        ("auth", "Group"),
        ("core", "User"),
        ("admin", "LogEntry"),
        ("sessions", "Session"),
        # Core app models (independent first)
        ("core", "State"),
        ("core", "Source"),
        ("core", "ContactRequest"),
        ("core", "Location"),
        # Core app models (dependent)
        ("core", "City"),
        ("core", "Parish"),
        ("core", "Contact"),
        ("core", "Schedule"),
    ]

    print("\n" + "=" * 80)
    print("Starting data migration from PostgreSQL to SQLite")
    print("=" * 80 + "\n")

    for app_label, model_name in models_to_copy:
        try:
            Model = apps.get_model(app_label, model_name)

            # Get all objects from source database
            source_objects = list(Model.objects.using(source_db).all())
            count = len(source_objects)

            if count == 0:
                print(f"  ✓ {app_label}.{model_name}: 0 records (skipped)")
                continue

            # Get all field names for the model
            field_names = [
                field.name
                for field in Model._meta.get_fields()
                if not field.many_to_many and not field.one_to_many
            ]

            # Prepare objects for bulk creation with explicit field values
            objects_to_create = []
            for source_obj in source_objects:
                # Create a new instance with the same field values
                field_values = {}
                for field_name in field_names:
                    try:
                        field_values[field_name] = getattr(source_obj, field_name)
                    except AttributeError:
                        # Field might not be directly accessible (reverse relations, etc.)
                        pass

                # Create new object with explicit PK
                new_obj = Model(**field_values)
                new_obj._state.adding = True
                new_obj._state.db = target_db
                objects_to_create.append(new_obj)

            # Bulk create in target database
            Model.objects.using(target_db).bulk_create(
                objects_to_create, batch_size=1000, ignore_conflicts=False
            )

            print(f"  ✓ {app_label}.{model_name}: {count} records copied")

        except LookupError:
            # Model doesn't exist in this migration state
            print(f"  ⊗ {app_label}.{model_name}: Model not found (skipped)")
            continue
        except Exception as e:
            print(f"  ✗ {app_label}.{model_name}: ERROR - {str(e)}")
            raise

    # Handle ManyToMany relationships for User model (groups and permissions)
    print("\nCopying ManyToMany relationships...")

    try:
        User = apps.get_model("core", "User")

        # Copy user groups
        users_source = User.objects.using(source_db).prefetch_related("groups").all()
        for user in users_source:
            user_target = User.objects.using(target_db).get(pk=user.pk)
            group_ids = list(user.groups.values_list("id", flat=True))
            if group_ids:
                user_target.groups.set(group_ids, using=target_db)

        # Copy user permissions
        users_source = (
            User.objects.using(source_db).prefetch_related("user_permissions").all()
        )
        for user in users_source:
            user_target = User.objects.using(target_db).get(pk=user.pk)
            permission_ids = list(user.user_permissions.values_list("id", flat=True))
            if permission_ids:
                user_target.user_permissions.set(permission_ids, using=target_db)

        print("  ✓ User ManyToMany relationships copied")

    except Exception as e:
        print(f"  ✗ User ManyToMany relationships: ERROR - {str(e)}")
        # Don't raise here - groups/permissions might be empty

    # Handle ManyToMany for Group model (permissions)
    try:
        Group = apps.get_model("auth", "Group")
        groups_source = (
            Group.objects.using(source_db).prefetch_related("permissions").all()
        )

        for group in groups_source:
            group_target = Group.objects.using(target_db).get(pk=group.pk)
            permission_ids = list(group.permissions.values_list("id", flat=True))
            if permission_ids:
                group_target.permissions.set(permission_ids, using=target_db)

        print("  ✓ Group ManyToMany relationships copied")

    except Exception as e:
        print(f"  ✗ Group ManyToMany relationships: ERROR - {str(e)}")

    print("\n" + "=" * 80)
    print("Data migration completed successfully!")
    print("=" * 80 + "\n")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration: Delete all data from SQLite database.
    WARNING: This will delete all data in the SQLite database.
    """
    # Skip during tests
    db_name = schema_editor.connection.settings_dict.get("NAME", "")
    if "test" in db_name.lower():
        print("\n⊗ Skipping reverse data migration during test run\n")
        return

    source_db = "default"  # PostgreSQL
    target_db = "new"  # SQLite
    current_db = schema_editor.connection.alias

    # Skip if not running on the source database
    if current_db == target_db:
        print(
            f"\n⊗ Skipping reverse data migration when running on target database '{target_db}'\n"
        )
        return

    if current_db != source_db:
        print(f"\n⊗ Skipping reverse data migration on database '{current_db}'\n")
        return

    # Models to delete in reverse dependency order
    models_to_delete = [
        ("core", "Schedule"),
        ("core", "Contact"),
        ("core", "Parish"),
        ("core", "City"),
        ("core", "Location"),
        ("core", "ContactRequest"),
        ("core", "Source"),
        ("core", "State"),
        ("sessions", "Session"),
        ("admin", "LogEntry"),
        ("core", "User"),
        ("auth", "Group"),
        ("auth", "Permission"),
        ("contenttypes", "ContentType"),
    ]

    print("\n" + "=" * 80)
    print("Reversing data migration: Deleting data from SQLite")
    print("=" * 80 + "\n")

    for app_label, model_name in models_to_delete:
        try:
            Model = apps.get_model(app_label, model_name)
            count = Model.objects.using(target_db).count()
            Model.objects.using(target_db).all().delete()
            print(f"  ✓ {app_label}.{model_name}: {count} records deleted")
        except LookupError:
            print(f"  ⊗ {app_label}.{model_name}: Model not found (skipped)")
            continue
        except Exception as e:
            print(f"  ✗ {app_label}.{model_name}: ERROR - {str(e)}")

    print("\n" + "=" * 80)
    print("Reverse migration completed!")
    print("=" * 80 + "\n")


class Migration(migrations.Migration):

    dependencies = [
        (
            "core",
            "0032_add_google_place_id_to_location_squashed_0036_rename_google_place_id_location_google_maps_place_id",
        ),
    ]

    operations = [
        migrations.RunPython(
            copy_data_postgres_to_sqlite,
            reverse_migration,
        ),
    ]
