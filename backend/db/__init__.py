"""
Database package for WhatsApp Task Manager.
Provides database connection management and core functionality.
"""

import sqlite3
import os
import config
from contextlib import contextmanager
from datetime import datetime


@contextmanager
def get_db_connection():
    """
    Get a database connection with automatic cleanup.
    
    This context manager ensures connections are properly closed
    even if an exception occurs.
    
    Yields:
        sqlite3.Connection: Database connection
    """
    conn = None
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def convert_to_iso8601(timestamp_str):
    """
    Convert SQLite timestamp string to ISO 8601 format with UTC timezone.
    
    SQLite CURRENT_TIMESTAMP returns UTC time in format: 'YYYY-MM-DD HH:MM:SS'
    This function converts it to ISO 8601 with explicit timezone: 'YYYY-MM-DDTHH:MM:SS.000Z'
    
    Args:
        timestamp_str (str): SQLite timestamp string or None
        
    Returns:
        str: ISO 8601 formatted timestamp with UTC timezone or None
        
    Examples:
        >>> convert_to_iso8601('2026-01-29 16:44:47')
        '2026-01-29T16:44:47.000Z'
        >>> convert_to_iso8601(None)
        None
    """
    if not timestamp_str:
        return None
    
    try:
        # Handle integer timestamps (invalid data)
        if isinstance(timestamp_str, int):
            print(f"⚠️  Warning: Invalid integer timestamp '{timestamp_str}', returning None")
            return None
        
        # Parse SQLite timestamp format (UTC)
        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        # Return ISO 8601 format with explicit UTC timezone
        return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    except (ValueError, TypeError) as e:
        print(f"⚠️  Warning: Failed to convert timestamp '{timestamp_str}': {e}")
        # Return original string for invalid formats (preserves backward compatibility)
        return timestamp_str


def init_database():
    """
    Initialize the database with required tables and indexes.
    Creates tables if they don't exist.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create employees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                start_date TEXT,
                end_date TEXT,
                color TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create project_employees junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_employees (
                project_id TEXT NOT NULL,
                employee_id INTEGER NOT NULL,
                PRIMARY KEY (project_id, employee_id),
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """)
        
        # Create tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                employee_id INTEGER,
                project_id TEXT,
                due_date TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'ready_to_start',
                whatsapp_sent BOOLEAN DEFAULT 0,
                whatsapp_response TEXT,
                response_notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # Create sequences table for ID generation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sequences (
                name TEXT PRIMARY KEY,
                current_value INTEGER NOT NULL DEFAULT 0
            )
        """)
        
        # Initialize sequences if they don't exist
        cursor.execute("""
            INSERT OR IGNORE INTO sequences (name, current_value) 
            VALUES ('project', 1), ('task', 1)
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_employees_phone ON employees(phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_id ON projects(id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON tasks(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_employee_id ON tasks(employee_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)")
        
        # Run migrations for rich task communication features
        _run_migrations(cursor)
        
        conn.commit()
        print("✅ Database initialized successfully")


def _run_migrations(cursor):
    """
    Run all pending migrations in order.
    Migrations are idempotent and safe to run multiple times.
    """
    import os
    
    migrations = [
        '20260127_add_activity_tables.sql',  # Phase 1: Activity feed
    ]
    
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    
    for migration_name in migrations:
        migration_file = os.path.join(migrations_dir, migration_name)
        
        if os.path.exists(migration_file):
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            # Execute the entire migration as one script
            # SQLite can handle multiple statements separated by semicolons
            try:
                cursor.executescript(migration_sql)
                print(f"✅ Migration applied: {migration_name}")
            except Exception as e:
                print(f"❌ Error executing migration {migration_name}: {e}")
                raise
        else:
            print(f"⚠️ Migration file not found: {migration_name}")
    
    # Run Phase 2 migration (requires special handling for ALTER TABLE)
    _run_phase2_migration(cursor)


def _run_phase2_migration(cursor):
    """
    Run Phase 2 migration with proper column existence checking.
    SQLite doesn't support ALTER TABLE ... ADD COLUMN IF NOT EXISTS,
    so we need to check column existence first.
    """
    import os
    
    # Check which columns already exist in task_messages
    cursor.execute("PRAGMA table_info(task_messages)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Define columns to add
    columns_to_add = {
        'delivered_at': 'DATETIME',
        'read_at': 'DATETIME',
        'failed_at': 'DATETIME',
        'failure_reason': 'TEXT',
        'read_receipt_available': 'BOOLEAN DEFAULT NULL',
        'read_inferred': 'BOOLEAN DEFAULT 0'
    }
    
    # Add missing columns
    for col_name, col_type in columns_to_add.items():
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE task_messages ADD COLUMN {col_name} {col_type}")
                print(f"  ✅ Added column: task_messages.{col_name}")
            except Exception as e:
                print(f"  ⚠️ Error adding column {col_name}: {e}")
        else:
            print(f"  ℹ️ Column already exists: task_messages.{col_name}")
    
    # Check and add columns to task_activities
    cursor.execute("PRAGMA table_info(task_activities)")
    existing_activity_columns = {row[1] for row in cursor.fetchall()}
    
    activity_columns = {
        'mention_notification_sent': 'BOOLEAN DEFAULT 0',
        'mention_notification_message_id': 'TEXT'
    }
    
    for col_name, col_type in activity_columns.items():
        if col_name not in existing_activity_columns:
            try:
                cursor.execute(f"ALTER TABLE task_activities ADD COLUMN {col_name} {col_type}")
                print(f"  ✅ Added column: task_activities.{col_name}")
            except Exception as e:
                print(f"  ⚠️ Error adding column {col_name}: {e}")
        else:
            print(f"  ℹ️ Column already exists: task_activities.{col_name}")
    
    # Check and add file_hash column to task_activity_attachments
    cursor.execute("PRAGMA table_info(task_activity_attachments)")
    existing_attachment_columns = {row[1] for row in cursor.fetchall()}
    
    if 'file_hash' not in existing_attachment_columns:
        try:
            cursor.execute("ALTER TABLE task_activity_attachments ADD COLUMN file_hash TEXT")
            print(f"  ✅ Added column: task_activity_attachments.file_hash")
        except Exception as e:
            print(f"  ⚠️ Error adding file_hash column: {e}")
    else:
        print(f"  ℹ️ Column already exists: task_activity_attachments.file_hash")
    
    # Now run the rest of the migration (CREATE TABLE IF NOT EXISTS statements)
    # This includes pending_clarifications with temp_file_path and cancelled_at columns
    migration_file = os.path.join(
        os.path.dirname(__file__), 
        'migrations', 
        '20260129_phase2_message_status.sql'
    )
    
    if os.path.exists(migration_file):
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        try:
            cursor.executescript(migration_sql)
            print("✅ Migration applied: 20260129_phase2_message_status.sql")
        except Exception as e:
            print(f"❌ Error executing Phase 2 migration: {e}")
            raise
    else:
        print("⚠️ Phase 2 migration file not found")


# Export the core functions that other modules need
__all__ = ['get_db_connection', 'init_database']