"""
Project CRUD operations for the database.
"""

from . import get_db_connection


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
                SELECT id, name, description, start_date, end_date, color, created_at
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
                SELECT id, name, description, start_date, end_date, color, created_at
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
            - name (str): Project name (required)
            - description (str): Project description (optional)
            - startDate (str): ISO date string (optional)
            - endDate (str): ISO date string (optional)
            - teamMembers (list): List of employee IDs to assign (optional)
            
    Returns:
        dict: Success response with created project (including generated ID) or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Generate unique project_id using sequence table
            cursor.execute("UPDATE sequences SET current_value = current_value + 1 WHERE name = 'project'")
            cursor.execute("SELECT current_value FROM sequences WHERE name = 'project'")
            result = cursor.fetchone()
            next_id = result[0] if result else 1
            project_id = f"proj_{str(next_id).zfill(3)}"
            
            # Insert project
            cursor.execute("""
                INSERT INTO projects (id, name, description, start_date, end_date, color)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                project_data['name'],
                project_data.get('description', ''),
                project_data.get('startDate', ''),
                project_data.get('endDate', ''),
                project_data.get('color', '#3B82F6')
            ))
            
            # Insert project-employee relationships
            # Accept both 'teamMembers' and 'assignedEmployees' (camelCase from frontend)
            team_members = project_data.get('teamMembers') or project_data.get('assignedEmployees', [])
            if team_members:
                for emp_id in team_members:
                    cursor.execute("""
                        INSERT INTO project_employees (project_id, employee_id)
                        VALUES (?, ?)
                    """, (project_id, emp_id))
            
            conn.commit()
            
            # Return properly formatted response
            response_data = {
                'id': project_id,
                'name': project_data['name'],
                'description': project_data.get('description', ''),
                'start_date': project_data.get('startDate', ''),
                'end_date': project_data.get('endDate', ''),
                'color': project_data.get('color', '#3B82F6'),
                'assigned_employees': team_members
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
                SELECT id, name, description, start_date, end_date, color, created_at
                FROM projects WHERE id = ?
            """, (project_id,))
            existing = cursor.fetchone()
            
            if not existing:
                return {"success": False, "error": "Project not found"}
            
            # Merge existing data with updates
            updated_name = project_data.get('name') or existing[1]
            updated_description = project_data.get('description', existing[2])  # Allow empty string
            updated_start = project_data.get('startDate') or existing[3]
            updated_end = project_data.get('endDate') or existing[4]
            updated_color = project_data.get('color') or existing[5]
            
            # Update project
            cursor.execute("""
                UPDATE projects
                SET name = ?, description = ?, start_date = ?, end_date = ?, color = ?
                WHERE id = ?
            """, (updated_name, updated_description, updated_start, updated_end, updated_color, project_id))
            
            # Update project-employee relationships if provided
            # Accept both 'teamMembers' and 'assignedEmployees' (camelCase from frontend)
            team_members = project_data.get('teamMembers')
            if team_members is None:
                team_members = project_data.get('assignedEmployees')
            
            if team_members is not None:
                # Delete existing relationships
                cursor.execute("""
                    DELETE FROM project_employees
                    WHERE project_id = ?
                """, (project_id,))
                
                # Insert new relationships
                for emp_id in team_members:
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
            
            # Return the updated project data
            updated_project = {
                'id': project_id,
                'name': updated_name,
                'description': updated_description,
                'start_date': updated_start,
                'end_date': updated_end,
                'color': updated_color,
                'created_at': existing[6],
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