"""
Test script to verify database schema creation.

This script tests that:
1. Database connection works
2. Schema can be created without errors
3. All expected tables exist
4. Indexes are created correctly
"""

import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql

# Import init_db functions
sys.path.insert(0, str(Path(__file__).parent))
from init_db import get_database_url, parse_database_url


def test_connection():
    """Test database connection."""
    print("Testing database connection...")
    
    db_url = get_database_url()
    conn_params = parse_database_url(db_url)
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✓ Connected to PostgreSQL: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_tables_exist():
    """Test that all expected tables exist."""
    print("\nTesting table existence...")
    
    expected_tables = [
        "users",
        "meetings",
        "participants",
        "recordings",
        "transcripts",
        "sign_language_captions",
        "ml_experiments",
        "ml_runs",
        "model_versions",
        "drift_metrics",
        "analytics_events"
    ]
    
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
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        all_exist = True
        for table in expected_tables:
            if table in existing_tables:
                print(f"✓ Table '{table}' exists")
            else:
                print(f"✗ Table '{table}' missing")
                all_exist = False
        
        cursor.close()
        conn.close()
        return all_exist
        
    except psycopg2.Error as e:
        print(f"✗ Error checking tables: {e}")
        return False


def test_indexes_exist():
    """Test that all expected indexes exist."""
    print("\nTesting index existence...")
    
    expected_indexes = [
        "idx_meetings_host_id",
        "idx_participants_meeting_id",
        "idx_participants_user_id",
        "idx_recordings_meeting_id",
        "idx_transcripts_recording_id",
        "idx_sign_language_captions_meeting_id",
        "idx_sign_language_captions_timestamp",
        "idx_ml_runs_experiment_id",
        "idx_model_versions_deployment_status",
        "idx_drift_metrics_model_version_id",
        "idx_drift_metrics_timestamp",
        "idx_analytics_events_meeting_id",
        "idx_analytics_events_timestamp"
    ]
    
    db_url = get_database_url()
    conn_params = parse_database_url(db_url)
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY indexname;
        """)
        
        existing_indexes = [row[0] for row in cursor.fetchall()]
        
        all_exist = True
        for index in expected_indexes:
            if index in existing_indexes:
                print(f"✓ Index '{index}' exists")
            else:
                print(f"✗ Index '{index}' missing")
                all_exist = False
        
        cursor.close()
        conn.close()
        return all_exist
        
    except psycopg2.Error as e:
        print(f"✗ Error checking indexes: {e}")
        return False


def test_foreign_keys():
    """Test that foreign key constraints exist."""
    print("\nTesting foreign key constraints...")
    
    db_url = get_database_url()
    conn_params = parse_database_url(db_url)
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            ORDER BY tc.table_name, kcu.column_name;
        """)
        
        foreign_keys = cursor.fetchall()
        
        if foreign_keys:
            print(f"✓ Found {len(foreign_keys)} foreign key constraints:")
            for fk in foreign_keys:
                print(f"  - {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")
        else:
            print("✗ No foreign key constraints found")
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error checking foreign keys: {e}")
        return False


def test_jsonb_columns():
    """Test that JSONB columns exist."""
    print("\nTesting JSONB columns...")
    
    expected_jsonb = [
        ("users", "settings"),
        ("meetings", "settings"),
        ("ml_runs", "hyperparameters"),
        ("ml_runs", "metrics"),
        ("model_versions", "performance_metrics"),
        ("drift_metrics", "metadata"),
        ("analytics_events", "event_data")
    ]
    
    db_url = get_database_url()
    conn_params = parse_database_url(db_url)
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        all_exist = True
        for table, column in expected_jsonb:
            cursor.execute("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                    AND table_name = %s
                    AND column_name = %s;
            """, (table, column))
            
            result = cursor.fetchone()
            if result and result[0] == 'jsonb':
                print(f"✓ JSONB column '{table}.{column}' exists")
            else:
                print(f"✗ JSONB column '{table}.{column}' missing or wrong type")
                all_exist = False
        
        cursor.close()
        conn.close()
        return all_exist
        
    except psycopg2.Error as e:
        print(f"✗ Error checking JSONB columns: {e}")
        return False


def run_all_tests():
    """Run all schema tests."""
    print("=" * 60)
    print("Database Schema Test Suite")
    print("=" * 60)
    
    tests = [
        ("Connection", test_connection),
        ("Tables", test_tables_exist),
        ("Indexes", test_indexes_exist),
        ("Foreign Keys", test_foreign_keys),
        ("JSONB Columns", test_jsonb_columns)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with exception: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Schema is valid.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
