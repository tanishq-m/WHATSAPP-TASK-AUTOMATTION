"""
Dashboard Service Module
Provides aggregated data for the owner dashboard overview.
Calculates project statistics, task summaries, and completion rates.
"""

import sys
sys.path.append('..')

from database import get_all_projects, get_all_tasks, get_all_employees, get_project_by_id
from datetime import datetime, date

print("📊 Dashboard service loaded")


def get_dashboard_summary():
    """
    Get overall dashboard statistics.
    
    Returns:
        dict: {
            "total_projects": int,
            "total_tasks": int,
            "tasks_by_status": {
                "ready_to_start": int,
                "in_progress": int,
                "pending_verification": int,
                "completed": int
            },
            "total_employees": int,
            "completion_rate": float  # Percentage of completed tasks
        }
    """
    try:
        print("📊 Calculating dashboard summary...")
        
        # Get all data from database
        projects_response = get_all_projects()
        tasks_response = get_all_tasks()  # Get all tasks across all projects
        employees_response = get_all_employees()
        
        # Extract data from responses
        projects = projects_response.get('data', []) if projects_response.get('success') else []
        tasks = tasks_response.get('data', []) if tasks_response.get('success') else []
        employees = employees_response.get('data', []) if employees_response.get('success') else []
        
        # Count projects
        total_projects = len(projects)
        
        # Count tasks by status
        tasks_by_status = {
            "ready_to_start": 0,
            "in_progress": 0,
            "pending_verification": 0,
            "completed": 0
        }
        
        for task in tasks:
            status = task.get('status', 'ready_to_start')
            if status in tasks_by_status:
                tasks_by_status[status] += 1
        
        # Calculate total tasks
        total_tasks = len(tasks)
        
        # Calculate completion rate
        completed_tasks = tasks_by_status["completed"]
        completion_rate = calculate_completion_rate(completed_tasks, total_tasks)
        
        # Count employees
        total_employees = len(employees)
        
        summary = {
            "total_projects": total_projects,
            "total_tasks": total_tasks,
            "tasks_by_status": tasks_by_status,
            "total_employees": total_employees,
            "completion_rate": completion_rate
        }
        
        print(f"✅ Dashboard summary: {total_projects} projects, {total_tasks} tasks, {completion_rate}% complete")
        return summary
        
    except Exception as e:
        print(f"❌ Error calculating dashboard summary: {e}")
        import traceback
        traceback.print_exc()
        # Return empty summary on error
        return {
            "total_projects": 0,
            "total_tasks": 0,
            "tasks_by_status": {
                "ready_to_start": 0,
                "in_progress": 0,
                "pending_verification": 0,
                "completed": 0
            },
            "total_employees": 0,
            "completion_rate": 0.0
        }


def get_projects_overview():
    """
    Get per-project statistics for dashboard cards.
    
    Returns:
        list: [{
            "project_id": str,
            "project_name": str,
            "project_color": str,
            "total_tasks": int,
            "completed_tasks": int,
            "in_progress_tasks": int,
            "pending_tasks": int,
            "overdue_tasks": int,
            "completion_rate": float,
            "start_date": str,
            "end_date": str,
            "assigned_employees": list[int],
            "last_activity": str  # ISO timestamp of last task update
        }]
    """
    try:
        print("📊 Calculating projects overview...")
        
        # Get all projects
        projects_response = get_all_projects()
        projects = projects_response.get('data', []) if projects_response.get('success') else []
        projects_overview = []
        
        for project in projects:
            project_id = project['id']
            
            # Get all tasks for this project
            tasks_response = get_all_tasks(project_id=project_id)
            project_tasks = tasks_response.get('data', []) if tasks_response.get('success') else []
            
            # Count tasks by status
            total_tasks = len(project_tasks)
            completed_tasks = sum(1 for task in project_tasks if task.get('status') == 'completed')
            in_progress_tasks = sum(1 for task in project_tasks if task.get('status') == 'in_progress')
            pending_tasks = sum(1 for task in project_tasks if task.get('status') in ['ready_to_start', 'pending_verification'])
            
            # Count overdue tasks
            overdue_tasks = sum(1 for task in project_tasks if is_task_overdue(task))
            
            # Calculate completion rate
            completion_rate = calculate_completion_rate(completed_tasks, total_tasks)
            
            # Get last activity timestamp
            last_activity = get_last_activity_timestamp(project_tasks)
            
            # Get assigned employees (unique employee IDs from all tasks)
            assigned_employees = list(set(
                task.get('employee_id') 
                for task in project_tasks 
                if task.get('employee_id')
            ))
            
            # Build project summary
            project_summary = {
                "project_id": project_id,
                "project_name": project.get('name', 'Unnamed Project'),
                "project_color": project.get('color', '#3B82F6'),  # Default blue
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "pending_tasks": pending_tasks,
                "overdue_tasks": overdue_tasks,
                "completion_rate": completion_rate,
                "start_date": project.get('start_date', ''),
                "end_date": project.get('end_date', ''),
                "assigned_employees": assigned_employees,
                "last_activity": last_activity
            }
            
            projects_overview.append(project_summary)
        
        # Sort by last_activity (most recent first)
        projects_overview.sort(key=lambda x: x['last_activity'] or '', reverse=True)
        
        print(f"✅ Projects overview: {len(projects_overview)} projects")
        return projects_overview
        
    except Exception as e:
        print(f"❌ Error calculating projects overview: {e}")
        import traceback
        traceback.print_exc()
        return []


def calculate_completion_rate(completed, total):
    """
    Helper to calculate completion percentage.
    
    Args:
        completed (int): Number of completed items
        total (int): Total number of items
        
    Returns:
        float: Completion percentage (0-100), rounded to 1 decimal place
    """
    if total == 0:
        return 0.0
    
    rate = (completed / total) * 100
    return round(rate, 1)


def is_task_overdue(task):
    """
    Check if task is overdue.
    
    Args:
        task (dict): Task object with status and due_date
        
    Returns:
        bool: True if task is overdue, False otherwise
    """
    try:
        # Completed tasks are never overdue
        if task.get('status') == 'completed':
            return False
        
        # Check if task has a due date
        due_date_str = task.get('due_date')
        if not due_date_str:
            return False
        
        # Parse due date
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            # Try alternative format
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
        
        # Compare with today
        today = date.today()
        return due_date < today
        
    except Exception as e:
        print(f"⚠️ Error checking if task is overdue: {e}")
        return False


def get_last_activity_timestamp(tasks):
    """
    Get the most recent activity timestamp from a list of tasks.
    
    Args:
        tasks (list): List of task objects
        
    Returns:
        str: ISO format timestamp of last activity, or empty string if no tasks
    """
    if not tasks:
        return ''
    
    try:
        # Get all updated_at timestamps
        timestamps = []
        for task in tasks:
            updated_at = task.get('updated_at')
            if updated_at:
                try:
                    # Parse timestamp
                    if isinstance(updated_at, str):
                        dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    else:
                        dt = updated_at
                    timestamps.append(dt)
                except:
                    continue
        
        if timestamps:
            # Return most recent timestamp
            most_recent = max(timestamps)
            return most_recent.isoformat()
        
        return ''
        
    except Exception as e:
        print(f"⚠️ Error getting last activity timestamp: {e}")
        return ''


# Test function (can be called directly)
if __name__ == "__main__":
    print("\n🧪 Testing dashboard service functions...")
    print("=" * 60)
    
    # Test dashboard summary
    summary = get_dashboard_summary()
    print("\nDashboard Summary:")
    print(f"  Projects: {summary['total_projects']}")
    print(f"  Tasks: {summary['total_tasks']}")
    print(f"  Completion Rate: {summary['completion_rate']}%")
    
    # Test projects overview
    projects = get_projects_overview()
    print(f"\nProjects Overview: {len(projects)} projects")
    for project in projects[:3]:  # Show first 3
        print(f"  - {project['project_name']}: {project['total_tasks']} tasks, {project['completion_rate']}% complete")
    
    print("\n✅ Dashboard service test complete!")
