"""
Database initialization script for Advanced Meeting Features.

This script creates all necessary tables and indexes in the PostgreSQL database.
"""

import os
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql


def get_database_url():
    """Get database URL from environment or use default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://meeting_user:meeting_pass@localhost:5432/meeting_db"
    )


def parse_database_url(url):
    """Parse PostgreSQL URL into connection parameters."""
    # Remove postgresql:// prefix
    url = url.replace("postgresql://", "")
    
    # Split user:pass@host:port/db
    if "@" in url:
        auth, rest = url.split("@", 1)
        user, password = auth.split(":", 1)
    else:
        raise ValueError("Invalid database URL format")
    
    if "/" in rest:
        host_port, dbname = rest.split("/", 1)
    else:
        raise ValueError("Invalid database URL format")
    
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host = host_port
        port = "5432"
    
    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password
    }


def init_database():
    """Initialize the database with schema."""
    print("Initializing database...")
    
    # Get database connection parameters
    db_url = get_database_url()
    print(f"Connecting to database: {db_url.split('@')[1]}")  # Hide credentials
    
    try:
        conn_params = parse_database_url(db_url)
    except ValueError as e:
        print(f"Error parsing database URL: {e}")
        sys.exit(1)
    
    # Connect to database
    try:
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()
        print("Connected successfully!")
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)
    
    # Read schema file
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}")
        sys.exit(1)
    
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    
    # Execute schema
    try:
        print("Creating tables and indexes...")
        cursor.execute(schema_sql)
        print("Database schema created successfully!")
    except psycopg2.Error as e:
        print(f"Error creating schema: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()
    
    print("Database initialization complete!")


def drop_all_tables():
    """Drop all tables (use with caution!)."""
    print("WARNING: This will drop all tables and data!")
    response = input("Are you sure? Type 'yes' to confirm: ")
    
    if response.lower() != "yes":
        print("Aborted.")
        return
    
    db_url = get_database_url()
    conn_params = parse_database_url(db_url)
    
    try:
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Drop tables in reverse order of dependencies
        tables = [
            "analytics_events",
            "drift_metrics",
            "model_versions",
            "ml_runs",
            "ml_experiments",
            "sign_language_captions",
            "transcripts",
            "recordings",
            "participants",
            "meetings",
            "users"
        ]
        
        for table in tables:
            try:
                cursor.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                    sql.Identifier(table)
                ))
                print(f"Dropped table: {table}")
            except psycopg2.Error as e:
                print(f"Error dropping table {table}: {e}")
        
        cursor.close()
        conn.close()
        print("All tables dropped successfully!")
        
    except psycopg2.Error as e:
        print(f"Error: {e}")
        sys.exit(1)


def check_tables():
    """Check which tables exist in the database."""
    db_url = get_database_url()
    conn_params = parse_database_url(db_url)
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print("Existing tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("No tables found in database.")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database management script")
    parser.add_argument(
        "command",
        choices=["init", "drop", "check"],
        help="Command to execute: init (create tables), drop (remove all tables), check (list tables)"
    )
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_database()
    elif args.command == "drop":
        drop_all_tables()
    elif args.command == "check":
        check_tables()
