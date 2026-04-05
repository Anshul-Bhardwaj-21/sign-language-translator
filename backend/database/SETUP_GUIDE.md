# Database Setup Guide

Quick guide to get the PostgreSQL database up and running for the Advanced Meeting Features system.

## Quick Start (Recommended)

The easiest way to set up the database is using Docker Compose, which automatically initializes the schema:

```bash
# Start PostgreSQL (schema is auto-initialized)
docker-compose up -d postgres

# Wait for database to be ready (about 10 seconds)
# The schema.sql file is automatically executed on first startup

# Verify tables were created
make db-check
```

That's it! The database is ready to use.

## Manual Initialization

If you need to manually initialize or reset the schema:

```bash
# Install Python dependencies (if not already installed)
pip install psycopg2-binary

# Initialize schema
make db-init

# Or use the Python script directly
python backend/database/init_db.py init
```

## Verify Installation

Run the test suite to verify everything is set up correctly:

```bash
make db-test
```

This will check:
- ✓ Database connection
- ✓ All 11 tables exist
- ✓ All 13 indexes are created
- ✓ Foreign key constraints are in place
- ✓ JSONB columns are configured

## Common Tasks

### Check Existing Tables

```bash
make db-check
```

### Access Database Shell

```bash
make db-shell
```

This opens a PostgreSQL interactive shell where you can run SQL queries:

```sql
-- List all tables
\dt

-- Describe a table
\d users

-- Query data
SELECT * FROM users;

-- Exit
\q
```

### Reset Database

**WARNING: This deletes all data!**

```bash
make db-reset
```

This will:
1. Stop the PostgreSQL container
2. Delete the database volume
3. Start a fresh PostgreSQL container
4. Auto-initialize the schema

## Connection Details

When running with Docker Compose:

- **Host**: `localhost` (from host machine) or `postgres` (from other containers)
- **Port**: `5432`
- **Database**: `meeting_db`
- **User**: `meeting_user`
- **Password**: `meeting_pass`

Connection string:
```
postgresql://meeting_user:meeting_pass@localhost:5432/meeting_db
```

## Environment Variables

The database connection is configured via the `DATABASE_URL` environment variable:

```bash
# In .env or docker-compose.yml
DATABASE_URL=postgresql://meeting_user:meeting_pass@postgres:5432/meeting_db
```

## Troubleshooting

### "Connection refused" error

The database container might not be running:

```bash
# Check container status
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart container
docker-compose restart postgres
```

### "Database does not exist" error

The database should be created automatically. If not:

```bash
# Reset and recreate
make db-reset
```

### "Permission denied" error

Make sure you're using the correct credentials from docker-compose.yml.

### Schema changes not applied

If you modified schema.sql and need to apply changes:

```bash
# Option 1: Reset database (deletes all data)
make db-reset

# Option 2: Apply changes manually
make db-shell
# Then paste your SQL changes
```

## Next Steps

After setting up the database:

1. **Create SQLAlchemy models** - Define Python models that map to these tables
2. **Set up migrations** - Use Alembic for schema version control
3. **Add seed data** - Create initial test users and meetings
4. **Configure connection pooling** - Optimize database connections
5. **Set up backups** - Implement backup and recovery procedures

## Schema Overview

The database includes:

### Core Tables (5)
- `users` - User accounts
- `meetings` - Meeting metadata
- `participants` - Meeting participants
- `recordings` - Video recordings
- `transcripts` - Speech transcripts

### AI/ML Tables (5)
- `sign_language_captions` - Sign language recognition results
- `ml_experiments` - MLflow experiments
- `ml_runs` - Training runs
- `model_versions` - Model registry
- `drift_metrics` - Production monitoring

### Analytics (1)
- `analytics_events` - Usage tracking

See [README.md](./README.md) for detailed schema documentation.

## Production Considerations

Before deploying to production:

1. **Change default credentials** - Use strong, unique passwords
2. **Enable SSL/TLS** - Encrypt connections
3. **Configure backups** - Set up automated backups
4. **Set up monitoring** - Monitor database health and performance
5. **Tune performance** - Adjust PostgreSQL configuration for your workload
6. **Implement migrations** - Use Alembic or similar for schema changes
7. **Set up replication** - Consider read replicas for scaling
8. **Configure connection pooling** - Use PgBouncer or similar

## Support

For issues or questions:

1. Check the [README.md](./README.md) for detailed documentation
2. Review the [schema.sql](./schema.sql) file
3. Run `make db-test` to diagnose issues
4. Check Docker logs: `docker-compose logs postgres`
