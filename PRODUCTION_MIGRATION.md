# Production Migration Guide: PostgreSQL to SQLite on Render

This guide explains how to migrate the production Missas.com.br application from PostgreSQL to SQLite on Render.

## Pre-Migration Checklist

- [ ] Backup current PostgreSQL database
- [ ] Review disk storage requirements (current data size)
- [ ] Plan for brief downtime during migration
- [ ] Test migration process in preview environment first

## Migration Steps

### 1. Export Data from PostgreSQL

Before making any changes, export all data from the current PostgreSQL database:

```bash
# Connect to your Render web service shell
# Run the export command
python manage.py migrate_db export /tmp/prod_backup.json

# Download the backup file to your local machine
# Use Render's web shell to copy the content or use render CLI
```

**Important**: Save this backup file securely. It contains all your production data.

### 2. Create Persistent Disk on Render

1. Go to your Render dashboard
2. Navigate to your web service
3. The render.yaml already includes the disk configuration:
   ```yaml
   disk:
     name: missas-db
     mountPath: /var/data
     sizeGB: 1
   ```
4. Render will automatically create this disk when you deploy the updated configuration

### 3. Update Environment Variables

In your Render web service settings:

1. Update `DATABASE_URL` to: `sqlite:////var/data/db.sqlite3`
2. This change will be applied automatically if you're using the render.yaml configuration

### 4. Deploy the Changes

1. Merge this PR to main branch
2. Render will automatically deploy the new configuration
3. During deployment:
   - The disk will be created (if it doesn't exist)
   - Django migrations will create the SQLite database schema
   - The database will be empty initially

### 5. Import Data to SQLite

After deployment completes:

1. Connect to Render web service shell
2. Upload your backup file (you may need to use render CLI or copy-paste method)
3. Run the import command:
   ```bash
   python manage.py migrate_db import /tmp/prod_backup.json
   ```
4. Verify the data was imported correctly:
   ```bash
   python manage.py shell -c "from missas.core.models import *; print(f'States: {State.objects.count()}, Cities: {City.objects.count()}, Parishes: {Parish.objects.count()}, Schedules: {Schedule.objects.count()}')"
   ```

### 6. Remove PostgreSQL Database (Optional)

After confirming everything works:

1. Keep the PostgreSQL database for a few days as a backup
2. Once confident, you can delete it from Render dashboard
3. This will save the database costs (~$7/month for starter plan)

## Rollback Plan

If something goes wrong:

1. Revert the DATABASE_URL to PostgreSQL connection string
2. Redeploy the previous version
3. The PostgreSQL database will still have all the data

## Post-Migration Verification

- [ ] Homepage loads correctly
- [ ] All parishes and schedules display properly
- [ ] Search and filtering work
- [ ] Admin panel accessible and functional
- [ ] Check Sentry for any errors

## Disk Space Management

Monitor disk usage:
```bash
# Check SQLite database size
ls -lh /var/data/db.sqlite3

# Check disk usage
df -h /var/data
```

The 1GB disk should be sufficient for thousands of parishes. To increase:
1. Update render.yaml with new sizeGB value
2. Redeploy

## Benefits Achieved

After migration:
- ✅ ~$7/month savings (no PostgreSQL starter plan cost)
- ✅ Simpler infrastructure (one service instead of two)
- ✅ Faster local development (no Docker required)
- ✅ Easy backups (single file)

## Support

If you encounter issues:
1. Check Render logs for errors
2. Verify DATABASE_URL environment variable
3. Ensure disk is properly mounted
4. Review MIGRATION.md for detailed command usage
