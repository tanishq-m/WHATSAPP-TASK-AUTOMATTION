"""
Database package for WhatsApp Task Manager.
Provides database connection management and core functionality.
"""

import sqlite3
import os
import config
from contextlib import contextmanager


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
        raise e
    finally:
        if conn:
            conn.close()


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
        
        # Run migration for activity tables (Stage 1.1)
        _run_activity_migration(cursor)
        
        conn.commit()
        print("✅ Database initialized successfully")


def _run_activity_migration(cursor):
    """
    Run migration to add activity tables for rich task communication.
    This is idempotent and safe to run multiple times.
    """
    import os
    
    migration_file = os.path.join(
        os.path.dirname(__file__), 
        'migrations', 
        '20260127_add_activity_tables.sql'
    )
    
    if os.path.exists(migration_file):
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute the entire migration as one script
        # SQLite can handle multiple statements separated by semicolons
        try:
            cursor.executescript(migration_sql)
            print("✅ Activity tables migration applied")
        except Exception as e:
            print(f"❌ Error executing migration: {e}")
            raise
    else:
        print("⚠️ Migration file not found, skipping activity tables")


# Export the core functions that other modules need
__all__ = ['get_db_connection', 'init_database']