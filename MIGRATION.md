# Database Migration Guide

This guide explains how to migrate data between PostgreSQL and SQLite databases.

## From PostgreSQL to SQLite

This is useful when migrating from a hosted PostgreSQL database (like Render's PostgreSQL) to SQLite with persistent disk storage.

### Steps:

1. **Export data from PostgreSQL**:
   ```bash
   # Set your PostgreSQL DATABASE_URL
   export DATABASE_URL="postgres://user:password@host:port/database"

   # Export all data to a JSON file
   python manage.py migrate_db export backup.json
   ```

2. **Switch to SQLite**:
   ```bash
   # Update your DATABASE_URL to use SQLite
   export DATABASE_URL="sqlite:///db.sqlite3"

   # Run migrations to create the SQLite database schema
   python manage.py migrate
   ```

3. **Import data into SQLite**:
   ```bash
   # Import the data from the backup
   python manage.py migrate_db import backup.json
   ```

## From SQLite to PostgreSQL

If you need to migrate back to PostgreSQL:

1. **Export data from SQLite**:
   ```bash
   export DATABASE_URL="sqlite:///db.sqlite3"
   python manage.py migrate_db export backup.json
   ```

2. **Switch to PostgreSQL**:
   ```bash
   export DATABASE_URL="postgres://user:password@host:port/database"
   python manage.py migrate
   ```

3. **Import data into PostgreSQL**:
   ```bash
   python manage.py migrate_db import backup.json
   ```

## Notes

- The migration command preserves all relationships and data integrity
- Make sure to backup your data before migration
- The export file can be large depending on your database size
- Models are exported/imported in the correct order to maintain foreign key relationships
