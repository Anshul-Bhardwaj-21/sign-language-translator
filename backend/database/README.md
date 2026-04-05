# Database Schema

This directory contains the PostgreSQL database schema for the Advanced Meeting Features system.

## Files

- `schema.sql` - Complete database schema with all tables and indexes
- `init_db.py` - Python script to initialize, drop, or check database tables
- `test_schema.py` - Unit tests for schema validation
- `test_property_roundtrip.py` - Property-based tests for JSONB round-trip consistency (**Validates: Requirements 25.4**)
- `PROPERTY_TESTS_README.md` - Detailed guide for running property-based tests

## Database Tables

### Core Tables

1. **users** - User accounts with authentication fields
2. **meetings** - Meeting metadata and settings (JSONB column for flexible configuration)
3. **participants** - Meeting participants with join/leave times and permissions
4. **recordings** - Meeting recordings with storage URLs and status
5. **transcripts** - Speech-to-text transcripts linked to recordings

### AI/ML Tables

6. **sign_language_captions** - Real-time sign language recognition results with confidence scores
7. **ml_experiments** - MLflow experiment tracking
8. **ml_runs** - Individual training runs with hyperparameters and metrics
9. **model_versions** - Versioned ML models with deployment status
10. **drift_metrics** - Production model monitoring and drift detection

### Analytics

11. **analytics_events** - Usage tracking and event logging

## Setup Instructions

### Using Docker Compose (Recommended)

The database is automatically created when you run:

```bash
docker-compose up postgres
```

Database credentials (from docker-compose.yml):
- Database: `meeting_db`
- User: `meeting_user`
- Password: `meeting_pass`
- Port: `5432`

### Initialize Schema

After the PostgreSQL container is running, initialize the schema:

```bash
# Install psycopg2 if not already installed
pip install psycopg2-binary

# Initialize database (create all tables)
python backend/database/init_db.py init

# Check existing tables
python backend/database/init_db.py check

# Drop all tables (WARNING: deletes all data)
python backend/database/init_db.py drop
```

### Manual Setup (Without Docker)

If you're running PostgreSQL locally:

1. Create the database:
```bash
createdb meeting_db
```

2. Set the DATABASE_URL environment variable:
```bash
export DATABASE_URL="postgresql://your_user:your_pass@localhost:5432/meeting_db"
```

3. Run the initialization script:
```bash
python backend/database/init_db.py init
```

## Schema Features

### JSONB Columns

The schema uses JSONB columns for flexible configuration:

- `users.settings` - User preferences and configuration
- `meetings.settings` - Meeting-specific settings (video quality, features enabled, etc.)
- `ml_runs.hyperparameters` - Training hyperparameters
- `ml_runs.metrics` - Training metrics (accuracy, loss, etc.)
- `model_versions.performance_metrics` - Model evaluation results
- `drift_metrics.metadata` - Additional drift detection metadata
- `analytics_events.event_data` - Flexible event data

### Indexes

Performance indexes are created for:
- Foreign key relationships
- Timestamp-based queries (for analytics and captions)
- Deployment status lookups (for model registry)
- Meeting and user lookups

### Cascading Deletes

The schema implements cascading deletes to maintain referential integrity:
- Deleting a meeting removes all participants, recordings, and captions
- Deleting a recording removes associated transcripts
- Deleting an experiment removes all runs

## Testing

### Unit Tests

Run schema validation tests:

```bash
python backend/database/test_schema.py
```

### Property-Based Tests

The database includes comprehensive property-based tests for JSONB round-trip consistency:

```bash
# Ensure database is running
docker compose up -d postgres

# Run property tests
python -m pytest backend/database/test_property_roundtrip.py -v
```

See `PROPERTY_TESTS_README.md` for detailed testing documentation.

## Requirements Mapping

This schema satisfies the following requirements from the spec:

- **25.4** - Meeting configuration round-trip serialization (tested by property tests)
- **26.1** - Sign language dataset structure (ml_experiments, ml_runs tables)
- **26.2** - Dataset metadata storage (JSONB columns)
- **26.11** - Model versioning (model_versions table)
- **51.2** - Experiment tracking (ml_experiments, ml_runs tables)
- **52.1** - Drift detection (drift_metrics table)

## Connection String Format

```
postgresql://[user]:[password]@[host]:[port]/[database]
```

Example:
```
postgresql://meeting_user:meeting_pass@localhost:5432/meeting_db
```

## Troubleshooting

### Connection Issues

If you can't connect to the database:

1. Check if PostgreSQL is running:
```bash
docker-compose ps postgres
```

2. Check logs:
```bash
docker-compose logs postgres
```

3. Verify connection parameters match docker-compose.yml

### Schema Errors

If table creation fails:

1. Check PostgreSQL version (requires 15+)
2. Ensure pgcrypto extension is available
3. Check for existing tables with conflicting names

### Reset Database

To completely reset the database:

```bash
# Drop all tables
python backend/database/init_db.py drop

# Recreate schema
python backend/database/init_db.py init
```

## Next Steps

After initializing the database:

1. Create database models in your application (SQLAlchemy, Prisma, etc.)
2. Implement database connection pooling
3. Set up migrations for schema changes (Alembic, Flyway, etc.)
4. Configure backup and recovery procedures
5. Set up monitoring and alerting for database health
