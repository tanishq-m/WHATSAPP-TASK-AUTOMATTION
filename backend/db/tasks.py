"""
Task CRUD operations for the database.
"""

from . import get_db_connection


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
            cursor.execute("UPDATE sequences SET current_value = current_value + 1 WHERE name = 'task'")
            cursor.execute("SELECT current_value FROM sequences WHERE name = 'task'")
            result = cursor.fetchone()
            next_id = result[0] if result else 1
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