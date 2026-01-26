"""
Database migrations and data seeding functions.
"""

from . import get_db_connection


def seed_employees():
    """
    Seed the employees table with test data.
    Only adds employees if the table is empty.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if employees table is empty
            cursor.execute("SELECT COUNT(*) FROM employees")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Add sample employees
                sample_employees = [
                    ("John Doe", "+918005800336", "Developer"),
                    ("Jane Smith", "+918005800337", "Designer"),
                    ("Mike Johnson", "+918005800338", "Manager"),
                    ("Sarah Wilson", "+918005800339", "QA Engineer"),
                    ("Alex Brown", "+918005800340", "DevOps Engineer")
                ]
                
                cursor.executemany("""
                    INSERT INTO employees (name, phone, role, created_at, updated_at)
                    VALUES (?, ?, ?, datetime('now'), datetime('now'))
                """, sample_employees)
                
                conn.commit()
                print(f"✅ Seeded {len(sample_employees)} employees")
            else:
                print(f"ℹ️ Employees table already has {count} records - skipping seed")
                
    except Exception as e:
        print(f"❌ Error seeding employees: {e}")


def migrate_status_values():
    """
    Migrate task status values to ensure consistency.
    Updates old status values to new standardized ones.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Map old status values to new ones
            status_mappings = {
                'todo': 'unassigned',
                'in_progress': 'in-progress',
                'done': 'completed',
                'pending': 'in-progress'
            }
            
            for old_status, new_status in status_mappings.items():
                cursor.execute("""
                    UPDATE tasks 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE status = ?
                """, (new_status, old_status))
                
                if cursor.rowcount > 0:
                    print(f"✅ Migrated {cursor.rowcount} tasks from '{old_status}' to '{new_status}'")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error migrating status values: {e}")


def sync_task_sequence():
    """
    Synchronize the task sequence with the highest existing task ID.
    Ensures new tasks get sequential IDs without conflicts.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Find the highest task ID number
            cursor.execute("""
                SELECT MAX(CAST(SUBSTR(task_id, 6) AS INTEGER)) as max_id
                FROM tasks 
                WHERE task_id LIKE 'task_%'
            """)
            
            result = cursor.fetchone()
            max_id = result[0] if result[0] is not None else 0
            
            # Update the sequence to be higher than the max existing ID
            next_id = max_id + 1
            cursor.execute("""
                UPDATE sequences 
                SET current_value = ?
                WHERE name = 'task'
            """, (next_id,))
            
            conn.commit()
            print(f"✅ Task sequence synchronized to {next_id}")
            
    except Exception as e:
        print(f"❌ Error syncing task sequence: {e}")


def sync_project_sequence():
    """
    Synchronize the project sequence with the highest existing project ID.
    Ensures new projects get sequential IDs without conflicts.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Find the highest project ID number
            cursor.execute("""
                SELECT MAX(CAST(SUBSTR(project_id, 9) AS INTEGER)) as max_id
                FROM projects 
                WHERE project_id LIKE 'project_%'
            """)
            
            result = cursor.fetchone()
            max_id = result[0] if result[0] is not None else 0
            
            # Update the sequence to be higher than the max existing ID
            next_id = max_id + 1
            cursor.execute("""
                UPDATE sequences 
                SET current_value = ?
                WHERE name = 'project'
            """, (next_id,))
            
            conn.commit()
            print(f"✅ Project sequence synchronized to {next_id}")
            
    except Exception as e:
        print(f"❌ Error syncing project sequence: {e}")