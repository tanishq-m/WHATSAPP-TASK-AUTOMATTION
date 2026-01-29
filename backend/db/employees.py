"""
Employee CRUD operations for the database.
"""

from . import get_db_connection
from utils.validators import validate_phone


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
                return {"success": False, "error": "Employee not found", "not_found": True}
        
    except Exception as e:
        print(f"❌ Error getting employee: {e}")
        return {"success": False, "error": str(e)}


def get_employee_by_phone(phone):
    """
    Get a single employee by phone number.
    
    Args:
        phone (str): Employee phone number (with or without + prefix)
        
    Returns:
        dict: Success response with employee data or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Normalize phone (remove + if present)
            normalized_phone = phone.replace('+', '')
            
            cursor.execute("""
                SELECT id, name, phone, role, created_at
                FROM employees
                WHERE REPLACE(phone, '+', '') = ?
            """, (normalized_phone,))
            
            employee = cursor.fetchone()
            
            if employee:
                print(f"✅ Retrieved employee {dict(employee)['name']} by phone")
                return {"success": True, "data": dict(employee)}
            else:
                print(f"❌ Employee not found for phone: {phone}")
                return {"success": False, "error": "Employee not found"}
        
    except Exception as e:
        print(f"❌ Error getting employee by phone: {e}")
        return {"success": False, "error": str(e)}


def create_employee(employee_data):
    """
    Create a new employee in the database.
    
    Args:
        employee_data (dict): Employee information
            - name (str): Employee name (required)
            - phone (str): Phone number with country code (required, unique)
            - role (str): Job role (required)
            
    Returns:
        dict: Success response with created employee or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Validate required fields
            if not employee_data.get('name') or not employee_data.get('name').strip():
                return {"success": False, "error": "Employee name is required"}
            
            if not employee_data.get('phone') or not employee_data.get('phone').strip():
                return {"success": False, "error": "Phone number is required"}
            
            if not employee_data.get('role') or not employee_data.get('role').strip():
                return {"success": False, "error": "Role is required"}
            
            # Validate phone format
            phone = employee_data['phone'].strip()
            if not validate_phone(phone):
                return {"success": False, "error": "Phone number must start with + and include country code (e.g., +919876543210)"}
            
            # Check phone uniqueness
            cursor.execute("SELECT id FROM employees WHERE phone = ?", (phone,))
            if cursor.fetchone():
                return {"success": False, "error": "Phone number already exists"}
            
            # Insert new employee
            cursor.execute("""
                INSERT INTO employees (name, phone, role)
                VALUES (?, ?, ?)
            """, (
                employee_data['name'].strip(),
                phone,
                employee_data['role'].strip()
            ))
            
            employee_id = cursor.lastrowid
            conn.commit()
            
            # Return created employee
            created_employee = {
                'id': employee_id,
                'name': employee_data['name'].strip(),
                'phone': phone,
                'role': employee_data['role'].strip(),
                'created_at': None  # Will be set by database
            }
            
            print(f"✅ Created employee: {created_employee['name']}")
            return {"success": True, "data": created_employee}
        
    except Exception as e:
        print(f"❌ Error creating employee: {e}")
        return {"success": False, "error": str(e)}


def update_employee(employee_id, employee_data):
    """
    Update an existing employee.
    
    Args:
        employee_id (int): Employee ID
        employee_data (dict): Updated employee information
            
    Returns:
        dict: Success response with updated employee or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check employee exists
            cursor.execute("SELECT id, name, phone, role FROM employees WHERE id = ?", (employee_id,))
            existing = cursor.fetchone()
            
            if not existing:
                return {"success": False, "error": "Employee not found"}
            
            # Prepare updates with existing values as fallback
            updated_name = employee_data.get('name', existing[1]).strip() if employee_data.get('name') else existing[1]
            updated_phone = employee_data.get('phone', existing[2]).strip() if employee_data.get('phone') else existing[2]
            updated_role = employee_data.get('role', existing[3]).strip() if employee_data.get('role') else existing[3]
            
            # Validate phone format if being updated
            if 'phone' in employee_data and employee_data['phone']:
                if not validate_phone(updated_phone):
                    return {"success": False, "error": "Phone number must start with + and include country code (e.g., +919876543210)"}
                
                # Check phone uniqueness if phone is changing
                if updated_phone != existing[2]:
                    cursor.execute("SELECT id FROM employees WHERE phone = ? AND id != ?", (updated_phone, employee_id))
                    if cursor.fetchone():
                        return {"success": False, "error": "Phone number already exists"}
            
            # Update employee
            cursor.execute("""
                UPDATE employees
                SET name = ?, phone = ?, role = ?
                WHERE id = ?
            """, (updated_name, updated_phone, updated_role, employee_id))
            
            conn.commit()
            
            # Return updated employee
            updated_employee = {
                'id': employee_id,
                'name': updated_name,
                'phone': updated_phone,
                'role': updated_role
            }
            
            print(f"✅ Updated employee: {updated_employee['name']}")
            return {"success": True, "data": updated_employee}
        
    except Exception as e:
        print(f"❌ Error updating employee: {e}")
        return {"success": False, "error": str(e)}


def delete_employee(employee_id):
    """
    Delete an employee and handle related data.
    
    Args:
        employee_id (int): Employee ID
            
    Returns:
        dict: Success response or error
        
    CRITICAL: Handle cascading effects:
        - Remove from project_employees junction table
        - Set tasks.employee_id to NULL where assigned to this employee
        - Update affected tasks status to 'unassigned'
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check employee exists
            cursor.execute("SELECT name FROM employees WHERE id = ?", (employee_id,))
            employee = cursor.fetchone()
            
            if not employee:
                return {"success": False, "error": "Employee not found"}
            
            employee_name = employee[0]
            
            # Get count of affected tasks for logging
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE employee_id = ?", (employee_id,))
            affected_tasks = cursor.fetchone()[0]
            
            # Remove from project_employees junction table
            cursor.execute("DELETE FROM project_employees WHERE employee_id = ?", (employee_id,))
            
            # Set tasks.employee_id to NULL and status to 'unassigned' for affected tasks
            cursor.execute("""
                UPDATE tasks 
                SET employee_id = NULL, status = 'unassigned'
                WHERE employee_id = ?
            """, (employee_id,))
            
            # Delete the employee
            cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
            
            conn.commit()
            
            print(f"✅ Deleted employee: {employee_name}")
            if affected_tasks > 0:
                print(f"📋 Updated {affected_tasks} tasks to unassigned status")
            
            return {"success": True, "message": f"Employee {employee_name} deleted successfully"}
        
    except Exception as e:
        print(f"❌ Error deleting employee: {e}")
        return {"success": False, "error": str(e)}