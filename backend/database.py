"""
Database module for WhatsApp Task Manager.
Handles all SQLite database operations including table creation,
CRUD operations for employees, projects, and tasks.
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager
from config import DATABASE_PATH

print("=" * 60)
print("📦 Database module loaded")
print(f"Database path: {DATABASE_PATH}")
print("=" * 60)


# ============================================================================
# DATABASE CONNECTION HELPER
# ============================================================================

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures connections are ALWAYS closed, even if an exception occurs.
    This prevents database locking issues.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees")
            # Connection is automatically closed when block exits
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn:
            conn.close()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_database():
    """
    Initialize the SQLite database and create all required tables.
    This function is idempotent - safe to call multiple times.
    
    Tables created:
    - employees: Store employee information
    - projects: Store project information
    - project_employees: Junction table for many-to-many relationship
    - tasks: Store task information with status tracking
    """
    try:
        print("\n🔧 Initializing database...")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Create employees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Employees table created/verified")
        
        # Create projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                start_date TEXT,
                end_date TEXT,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Projects table created/verified")
        
        # Create project_employees junction table (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_employees (
                project_id TEXT NOT NULL,
                employee_id INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                PRIMARY KEY (project_id, employee_id)
            )
        """)
        print("✅ Project_employees junction table created/verified")
        
        # Create sequences table for generating unique IDs that never decrease
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sequences (
                name TEXT PRIMARY KEY,
                current_value INTEGER DEFAULT 0
            )
        """)
        # Initialize task sequence if not exists
        cursor.execute("""
            INSERT OR IGNORE INTO sequences (name, current_value) VALUES ('task', 0)
        """)
        print("✅ Sequences table created/verified")
        
        # Create tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                employee_id INTEGER,
                due_date TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'unassigned',
                whatsapp_sent BOOLEAN DEFAULT 0,
                whatsapp_response TEXT,
                response_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """)
        print("✅ Tasks table created/verified")
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_project_id 
            ON tasks(project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_employee_id 
            ON tasks(employee_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status 
            ON tasks(status)
        """)
        print("✅ Database indexes created/verified")
        
        conn.commit()
        
        # Seed initial data (hardcoded employees)
        seed_employees(conn)
        
        # Run migrations to update existing data
        migrate_status_values(conn)
        
        # Sync sequence with existing task data
        sync_task_sequence(conn)
        
        conn.close()
        print("✅ Database initialization complete!\n")
        return {"success": True, "message": "Database initialized successfully"}
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return {"success": False, "error": str(e)}


def seed_employees(conn):
    """
    Seed the database with 3 hardcoded employees (MVP requirement).
    Only inserts if employees table is empty.
    
    Args:
        conn: SQLite connection object
    """
    try:
        cursor = conn.cursor()
        
        # Check if employees already exist
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"ℹ️  Employees already exist ({count} employees)")
            return
        
        # Insert hardcoded employees
        employees = [
            (1, "Rajesh Kumar", "+919876543210", "Developer"),
            (2, "Priya Singh", "+919876543211", "Designer"),
            (3, "Amit Patel", "+919876543212", "Tester")
        ]
        
        cursor.executemany("""
            INSERT INTO employees (id, name, phone, role)
            VALUES (?, ?, ?, ?)
        """, employees)
        
        conn.commit()
        print(f"✅ Seeded {len(employees)} employees")
        
    except Exception as e:
        print(f"❌ Error seeding employees: {e}")


def migrate_status_values(conn):
    """
    Migrate old status values to new ones (Phase 2 - Issue #3).
    Updates: ready_to_start -> unassigned
    
    Args:
        conn: SQLite connection object
    """
    try:
        cursor = conn.cursor()
        
        # Update old status values to new ones
        cursor.execute("""
            UPDATE tasks 
            SET status = 'unassigned' 
            WHERE status = 'ready_to_start'
        """)
        
        rows_updated = cursor.rowcount
        if rows_updated > 0:
            print(f"✅ Migrated {rows_updated} tasks from 'ready_to_start' to 'unassigned'")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error migrating status values: {e}")


def sync_task_sequence(conn):
    """
    Synchronize the task sequence counter with existing task data.
    Ensures sequence is always >= the highest existing task_id.
    This handles cases where tasks already exist in the database.
    
    Args:
        conn: SQLite connection object
    """
    try:
        cursor = conn.cursor()
        
        # Get the highest task_id number currently in use
        cursor.execute("SELECT MAX(CAST(SUBSTR(task_id, 6) AS INTEGER)) as max_id FROM tasks")
        result = cursor.fetchone()
        max_task_id = result[0] if result[0] else 0
        
        # Get current sequence value
        cursor.execute("SELECT current_value FROM sequences WHERE name = 'task'")
        result = cursor.fetchone()
        current_seq = result[0] if result else 0
        
        # Only update if existing tasks have higher IDs than sequence
        if max_task_id > current_seq:
            cursor.execute("UPDATE sequences SET current_value = ? WHERE name = 'task'", (max_task_id,))
            print(f"✅ Synced task sequence to {max_task_id}")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error syncing task sequence: {e}")


# ============================================================================
# EMPLOYEE OPERATIONS
# ============================================================================

def get_all_employees():
    """
    Get all employees from the database.
    
    Returns:
        dict: Success response with list of employees or error
        
    Example:
        {
            "success": True,
            "data": [
                {"id": 1, "name": "Rajesh Kumar", "phone": "+919876543210", ...},
                ...
            ]
        }
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, phone, role, created_at
                FROM employees
                ORDER BY name
            """)
            
            employees = [dict(row) for row in cursor.fetchall()]
            
            print(f"✅ Retrieved {len(employees)} employees")
            return {"success": True, "data": employees}
        
    except Exception as e:
        print(f"❌ Error getting employees: {e}")
        return {"success": False, "error": str(e)}


def get_employee_by_id(employee_id):
    """
    Get a single employee by ID.
    
    Args:
        employee_id (int): Employee ID
        
    Returns:
        dict: Success response with employee data or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, phone, role, created_at
                FROM employees
                WHERE id = ?
            """, (employee_id,))
            
            employee = cursor.fetchone()
            
            if employee:
                print(f"✅ Retrieved employee: {employee['name']}")
                return {"success": True, "data": dict(employee)}
            else:
                print(f"⚠️  Employee not found: ID {employee_id}")
                return {"success": False, "error": "Employee not found"}
        
    except Exception as e:
        print(f"❌ Error getting employee: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# PROJECT OPERATIONS
# ============================================================================

def get_all_projects():
    """
    Get all projects from the database with assigned employees.
    
    Returns:
        dict: Success response with list of projects or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, start_date, end_date, color, created_at
                FROM projects
                ORDER BY created_at DESC
            """)
            
            projects = [dict(row) for row in cursor.fetchall()]
            
            # Get assigned employees for each project
            for project in projects:
                cursor.execute("""
                    SELECT employee_id
                    FROM project_employees
                    WHERE project_id = ?
                """, (project['id'],))
                
                employee_ids = [row['employee_id'] for row in cursor.fetchall()]
                project['assigned_employees'] = employee_ids
            
            print(f"✅ Retrieved {len(projects)} projects with assigned employees")
            return {"success": True, "data": projects}
        
    except Exception as e:
        print(f"❌ Error getting projects: {e}")
        return {"success": False, "error": str(e)}


def get_project_by_id(project_id):
    """
    Get a single project by ID with assigned employees.
    
    Args:
        project_id (str): Project ID
        
    Returns:
        dict: Success response with project data including employees
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get project details
            cursor.execute("""
                SELECT id, name, start_date, end_date, color, created_at
                FROM projects
                WHERE id = ?
            """, (project_id,))
            
            project = cursor.fetchone()
            
            if not project:
                return {"success": False, "error": "Project not found"}
            
            project_dict = dict(project)
            
            # Get assigned employees for this project
            cursor.execute("""
                SELECT e.id, e.name, e.phone, e.role
                FROM employees e
                INNER JOIN project_employees pe ON e.id = pe.employee_id
                WHERE pe.project_id = ?
            """, (project_id,))
            
            employees = [dict(row) for row in cursor.fetchall()]
            project_dict['employees'] = employees
            
            print(f"✅ Retrieved project: {project_dict['name']}")
            return {"success": True, "data": project_dict}
        
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return {"success": False, "error": str(e)}


def create_project(project_data):
    """
    Create a new project in the database.
    
    Args:
        project_data (dict): Project information
            - id (str): Project ID (e.g., "proj_001")
            - name (str): Project name
            - start_date (str): ISO date string
            - end_date (str): ISO date string
            - color (str): Hex color code
            - employee_ids (list): List of employee IDs to assign
            
    Returns:
        dict: Success response with created project or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert project
            cursor.execute("""
                INSERT INTO projects (id, name, start_date, end_date, color)
                VALUES (?, ?, ?, ?, ?)
            """, (
                project_data['id'],
                project_data['name'],
                project_data.get('startDate', ''),
                project_data.get('endDate', ''),
                project_data.get('color', '#3B82F6')
            ))
            
            # Insert project-employee relationships
            # Accept both 'employeeIds' and 'assignedEmployees' (camelCase from frontend)
            employee_ids = project_data.get('employeeIds') or project_data.get('assignedEmployees', [])
            if employee_ids:
                for emp_id in employee_ids:
                    cursor.execute("""
                        INSERT INTO project_employees (project_id, employee_id)
                        VALUES (?, ?)
                    """, (project_data['id'], emp_id))
            
            conn.commit()
            
            # Return properly formatted response with assigned_employees
            response_data = {
                'id': project_data['id'],
                'name': project_data['name'],
                'start_date': project_data.get('startDate', ''),
                'end_date': project_data.get('endDate', ''),
                'color': project_data.get('color', '#3B82F6'),
                'assigned_employees': employee_ids or []
            }
            
            print(f"✅ Created project: {project_data['name']}")
            return {"success": True, "data": response_data}
        
    except Exception as e:
        print(f"❌ Error creating project: {e}")
        return {"success": False, "error": str(e)}


def update_project(project_id, project_data):
    """
    Update an existing project.
    
    Args:
        project_id (str): Project ID
        project_data (dict): Updated project information
        
    Returns:
        dict: Success response with updated project data or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # First, get the existing project to merge with updates
            cursor.execute("""
                SELECT id, name, start_date, end_date, color, created_at
                FROM projects WHERE id = ?
            """, (project_id,))
            existing = cursor.fetchone()
            
            if not existing:
                return {"success": False, "error": "Project not found"}
            
            # Merge existing data with updates
            updated_name = project_data.get('name') or existing[1]
            updated_start = project_data.get('startDate') or existing[2]
            updated_end = project_data.get('endDate') or existing[3]
            updated_color = project_data.get('color') or existing[4]
            
            # Update project
            cursor.execute("""
                UPDATE projects
                SET name = ?, start_date = ?, end_date = ?, color = ?
                WHERE id = ?
            """, (updated_name, updated_start, updated_end, updated_color, project_id))
            
            # Update project-employee relationships if provided
            # Accept both 'employeeIds' and 'assignedEmployees' (camelCase from frontend)
            employee_ids = project_data.get('employeeIds') or project_data.get('assignedEmployees')
            if employee_ids is not None:
                # Delete existing relationships
                cursor.execute("""
                    DELETE FROM project_employees
                    WHERE project_id = ?
                """, (project_id,))
                
                # Insert new relationships
                for emp_id in employee_ids:
                    cursor.execute("""
                        INSERT INTO project_employees (project_id, employee_id)
                        VALUES (?, ?)
                    """, (project_id, emp_id))
            
            conn.commit()
            
            # Fetch the current assigned employees
            cursor.execute("""
                SELECT employee_id FROM project_employees
                WHERE project_id = ?
            """, (project_id,))
            assigned_employees = [row[0] for row in cursor.fetchall()]
            
            # Return the updated project data with assigned_employees
            updated_project = {
                'id': project_id,
                'name': updated_name,
                'start_date': updated_start,
                'end_date': updated_end,
                'color': updated_color,
                'created_at': existing[5],
                'assigned_employees': assigned_employees
            }
            
            print(f"✅ Updated project: {project_id}")
            return {"success": True, "data": updated_project, "message": "Project updated successfully"}
        
    except Exception as e:
        print(f"❌ Error updating project: {e}")
        return {"success": False, "error": str(e)}


def delete_project(project_id):
    """
    Delete a project and all its associated data.
    
    Args:
        project_id (str): Project ID
        
    Returns:
        dict: Success response or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if project exists first
            cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
            if not cursor.fetchone():
                print(f"⚠️ Project not found: {project_id}")
                return {"success": False, "error": "Project not found", "not_found": True}
            
            # Delete project-employee relationships
            cursor.execute("""
                DELETE FROM project_employees
                WHERE project_id = ?
            """, (project_id,))
            
            # Delete tasks associated with project
            cursor.execute("""
                DELETE FROM tasks
                WHERE project_id = ?
            """, (project_id,))
            
            # Delete project
            cursor.execute("""
                DELETE FROM projects
                WHERE id = ?
            """, (project_id,))
            
            conn.commit()
            
            print(f"✅ Deleted project: {project_id}")
            return {"success": True, "message": "Project deleted successfully"}
        
    except Exception as e:
        print(f"❌ Error deleting project: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# TASK OPERATIONS
# ============================================================================

def create_task(task_data):
    """
    Create a new task in the database.
    
    Args:
        task_data (dict): Task data with keys:
            - title (str): Task title
            - description (str): Task description
            - projectId (str): Project ID
            - assignedTo (int): Employee ID
            - dueDate (str): Due date (ISO format)
            - priority (str): Priority level (high, medium, low)
            - status (str): Task status
            
    Returns:
        dict: Success response with created task or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Generate unique task_id using sequence table (never decreases, even after deletions)
            # This atomic operation increments the counter and returns the new value
            cursor.execute("UPDATE sequences SET current_value = current_value + 1 WHERE name = 'task'")
            cursor.execute("SELECT current_value FROM sequences WHERE name = 'task'")
            result = cursor.fetchone()
            next_id = result['current_value'] if result else 1
            task_id = f"task_{str(next_id).zfill(3)}"
            
            # Insert task
            cursor.execute("""
                INSERT INTO tasks (
                    task_id, project_id, title, description, 
                    employee_id, due_date, priority, status,
                    whatsapp_sent, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                task_id,
                task_data.get('projectId'),
                task_data.get('title'),
                task_data.get('description', ''),
                task_data.get('assignedTo'),
                task_data.get('dueDate'),
                task_data.get('priority', 'medium'),
                task_data.get('status', 'unassigned')
            ))
            
            conn.commit()
            
            # Fetch the created task with employee info
            cursor.execute("""
                SELECT t.*, e.name as employee_name, e.phone as employee_phone
                FROM tasks t
                LEFT JOIN employees e ON t.employee_id = e.id
                WHERE t.task_id = ?
            """, (task_id,))
            
            task = dict(cursor.fetchone())
            
            print(f"✅ Created task: {task_id}")
            return {"success": True, "data": task}
        
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return {"success": False, "error": str(e)}


def get_all_tasks(project_id=None):
    """
    Get all tasks, optionally filtered by project.
    
    Args:
        project_id (str, optional): Filter by project ID
        
    Returns:
        dict: Success response with list of tasks or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if project_id:
                cursor.execute("""
                    SELECT t.*, e.name as employee_name, e.phone as employee_phone
                    FROM tasks t
                    LEFT JOIN employees e ON t.employee_id = e.id
                    WHERE t.project_id = ?
                    ORDER BY t.created_at DESC
                """, (project_id,))
            else:
                cursor.execute("""
                    SELECT t.*, e.name as employee_name, e.phone as employee_phone
                    FROM tasks t
                    LEFT JOIN employees e ON t.employee_id = e.id
                    ORDER BY t.created_at DESC
                """)
            
            tasks = [dict(row) for row in cursor.fetchall()]
            
            print(f"✅ Retrieved {len(tasks)} tasks")
            return {"success": True, "data": tasks}
        
    except Exception as e:
        print(f"❌ Error getting tasks: {e}")
        return {"success": False, "error": str(e)}


def get_task_by_id(task_id):
    """
    Get a single task by ID.
    
    Args:
        task_id (str): Task ID
        
    Returns:
        dict: Success response with task data or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT t.*, e.name as employee_name, e.phone as employee_phone
                FROM tasks t
                LEFT JOIN employees e ON t.employee_id = e.id
                WHERE t.task_id = ?
            """, (task_id,))
            
            task = cursor.fetchone()
            
            if task:
                print(f"✅ Retrieved task: {task_id}")
                return {"success": True, "data": dict(task)}
            else:
                print(f"⚠️ Task not found: {task_id}")
                return {"success": False, "error": "Task not found"}
        
    except Exception as e:
        print(f"❌ Error getting task: {e}")
        return {"success": False, "error": str(e)}


def update_task(task_id, updates):
    """
    Update a task's fields.
    
    Args:
        task_id (str): Task ID
        updates (dict): Dictionary of fields to update
        
    Returns:
        dict: Success response with updated task or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build dynamic update query
            update_fields = []
            update_values = []
            
            field_mapping = {
                'title': 'title',
                'description': 'description',
                'assignedTo': 'employee_id',
                'dueDate': 'due_date',
                'priority': 'priority',
                'status': 'status',
                'whatsappSent': 'whatsapp_sent',
                'whatsappResponse': 'whatsapp_response',
                'responseNotes': 'response_notes'
            }
            
            for key, db_field in field_mapping.items():
                if key in updates:
                    update_fields.append(f"{db_field} = ?")
                    update_values.append(updates[key])
            
            if not update_fields:
                return {"success": False, "error": "No fields to update"}
            
            # Always update updated_at
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            # Build and execute query
            query = f"""
                UPDATE tasks
                SET {', '.join(update_fields)}
                WHERE task_id = ?
            """
            update_values.append(task_id)
            
            cursor.execute(query, update_values)
            conn.commit()
            
            # Fetch updated task
            cursor.execute("""
                SELECT t.*, e.name as employee_name, e.phone as employee_phone
                FROM tasks t
                LEFT JOIN employees e ON t.employee_id = e.id
                WHERE t.task_id = ?
            """, (task_id,))
            
            task = cursor.fetchone()
            
            if task:
                print(f"✅ Updated task: {task_id}")
                return {"success": True, "data": dict(task)}
            else:
                return {"success": False, "error": "Task not found after update"}
        
    except Exception as e:
        print(f"❌ Error updating task: {e}")
        return {"success": False, "error": str(e)}


def delete_task(task_id):
    """
    Delete a task from the database.
    
    Args:
        task_id (str): Task ID to delete
        
    Returns:
        dict: Success response or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if task exists first
            cursor.execute("SELECT task_id FROM tasks WHERE task_id = ?", (task_id,))
            if not cursor.fetchone():
                print(f"⚠️ Task not found: {task_id}")
                return {"success": False, "error": "Task not found", "not_found": True}
            
            cursor.execute("""
                DELETE FROM tasks
                WHERE task_id = ?
            """, (task_id,))
            
            conn.commit()
            
            print(f"✅ Deleted task: {task_id}")
            return {"success": True, "message": "Task deleted successfully"}
        
    except Exception as e:
        print(f"❌ Error deleting task: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# INITIALIZE DATABASE ON MODULE LOAD
# ============================================================================

# Auto-initialize database when module is imported
init_database()
