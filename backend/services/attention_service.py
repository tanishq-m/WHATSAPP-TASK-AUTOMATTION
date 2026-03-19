"""
Attention Service Module
Detects tasks that need owner's attention based on various rules.
Prioritizes alerts by urgency (High/Medium) for dashboard overview.
"""

import sys
sys.path.append('..')

from database import get_all_tasks, get_all_projects, get_employee_by_id, get_project_by_id
from datetime import datetime, timedelta
import json

print("🚨 Attention service loaded")


def get_attention_items():
    """
    Get all tasks that need owner's attention.
    
    Returns:
        list: [{
            "task_id": str,
            "task_title": str,
            "project_id": str,
            "project_name": str,
            "employee_id": int,
            "employee_name": str,
            "employee_phone": str,
            "priority": str,  # "high" or "medium"
            "reason": str,  # Why it needs attention
            "due_date": str,
            "hours_since_update": float,
            "status": str
        }]
    """
    try:
        print("🚨 Checking for tasks needing attention...")
        
        # Get all tasks
        tasks_response = get_all_tasks()
        tasks = tasks_response.get('data', []) if tasks_response.get('success') else []
        
        attention_items = []
        
        for task in tasks:
            # Skip completed tasks
            if task.get('status') == 'completed':
                continue
            
            # Check each attention rule
            priority = None
            reason = None
            
            # Rule 1: Check if overdue (HIGH priority)
            is_overdue, overdue_reason = check_if_overdue(task)
            if is_overdue:
                priority = "high"
                reason = overdue_reason
            
            # Rule 2: Check for no response (HIGH or MEDIUM priority)
            if not priority:  # Only check if not already flagged
                no_response_priority, no_response_reason = check_no_response(task)
                if no_response_priority:
                    priority = no_response_priority
                    reason = no_response_reason
            
            # Rule 3: Check pending verification (MEDIUM priority)
            if not priority:  # Only check if not already flagged
                pending_priority, pending_reason = check_pending_verification(task)
                if pending_priority:
                    priority = pending_priority
                    reason = pending_reason
            
            # If task needs attention, add to list
            if priority and reason:
                # Enrich with project and employee details
                enriched_task = enrich_task_with_details(task, priority, reason)
                if enriched_task:
                    attention_items.append(enriched_task)
        
        # Sort by priority (high first) then by hours_since_update (oldest first)
        attention_items.sort(key=lambda x: (
            0 if x['priority'] == 'high' else 1,  # High priority first
            -x['hours_since_update']  # Oldest first (negative for descending)
        ))
        
        print(f"✅ Found {len(attention_items)} tasks needing attention")
        return attention_items
        
    except Exception as e:
        print(f"❌ Error getting attention items: {e}")
        import traceback
        traceback.print_exc()
        return []


def check_if_overdue(task):
    """
    Check if task is overdue.
    
    Args:
        task (dict): Task object
        
    Returns:
        tuple: (is_overdue: bool, reason: str)
    """
    try:
        # Completed tasks are never overdue
        if task.get('status') == 'completed':
            return (False, "")
        
        # Check if task has a due date
        due_date_str = task.get('due_date')
        if not due_date_str:
            return (False, "")
        
        # Parse due date
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            # Try alternative format
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
        
        # Compare with today
        today = datetime.now().date()
        if due_date < today:
            days_overdue = (today - due_date).days
            return (True, f"Task overdue by {days_overdue} day{'s' if days_overdue > 1 else ''}")
        
        return (False, "")
        
    except Exception as e:
        print(f"⚠️ Error checking if task is overdue: {e}")
        return (False, "")


def check_no_response(task):
    """
    Check if task has no response for a long time.
    
    Args:
        task (dict): Task object
        
    Returns:
        tuple: (priority: str or None, reason: str)
    """
    try:
        # Only check if task was sent via WhatsApp
        if not task.get('whatsapp_sent'):
            return (None, "")
        
        # Only check active statuses
        status = task.get('status')
        if status not in ['in_progress', 'pending_verification']:
            return (None, "")
        
        # Calculate hours since last update
        updated_at = task.get('updated_at')
        if not updated_at:
            return (None, "")
        
        hours_since = calculate_hours_since_update(updated_at)
        
        # Rule: No response for > 4 hours = HIGH priority
        if hours_since > 4:
            return ("high", f"No response for {int(hours_since)} hours")
        
        # Rule: No response for > 2 hours = MEDIUM priority
        if hours_since > 2:
            return ("medium", f"No response for {int(hours_since)} hours")
        
        return (None, "")
        
    except Exception as e:
        print(f"⚠️ Error checking no response: {e}")
        return (None, "")


def check_pending_verification(task):
    """
    Check if task stuck in pending verification.
    
    Args:
        task (dict): Task object
        
    Returns:
        tuple: (priority: str or None, reason: str)
    """
    try:
        # Only check pending_verification status
        if task.get('status') != 'pending_verification':
            return (None, "")
        
        # Calculate hours since last update
        updated_at = task.get('updated_at')
        if not updated_at:
            return (None, "")
        
        hours_since = calculate_hours_since_update(updated_at)
        
        # Rule: Pending for > 6 hours = MEDIUM priority
        if hours_since > 6:
            return ("medium", f"Pending verification for {int(hours_since)} hours")
        
        return (None, "")
        
    except Exception as e:
        print(f"⚠️ Error checking pending verification: {e}")
        return (None, "")


def calculate_hours_since_update(updated_at):
    """
    Calculate hours between updated_at and now.
    
    Args:
        updated_at (str): ISO format timestamp
        
    Returns:
        float: Hours since update, rounded to 1 decimal
    """
    try:
        # Parse timestamp
        if isinstance(updated_at, str):
            # Try ISO format first
            try:
                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except:
                # Try other formats
                dt = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
        else:
            dt = updated_at
        
        # Calculate difference
        now = datetime.now()
        if dt.tzinfo:
            # Make now timezone-aware
            from datetime import timezone
            now = datetime.now(timezone.utc)
        
        delta = now - dt
        hours = delta.total_seconds() / 3600
        
        return round(hours, 1)
        
    except Exception as e:
        print(f"⚠️ Error calculating hours since update: {e}")
        return 0.0


def enrich_task_with_details(task, priority, reason):
    """
    Enrich task with project and employee details.
    
    Args:
        task (dict): Task object
        priority (str): Priority level
        reason (str): Reason for attention
        
    Returns:
        dict: Enriched task or None if missing data
    """
    try:
        # Get project details
        project_id = task.get('project_id')
        project_response = get_project_by_id(project_id)
        project = project_response.get('data') if project_response.get('success') else None
        
        # Get employee details
        employee_id = task.get('employee_id')
        employee_response = get_employee_by_id(employee_id) if employee_id else None
        employee = employee_response.get('data') if employee_response and employee_response.get('success') else None
        
        # Calculate hours since update
        hours_since = calculate_hours_since_update(task.get('updated_at', ''))
        
        return {
            "task_id": task.get('id'),
            "task_title": task.get('title', 'Untitled Task'),
            "project_id": project_id,
            "project_name": project.get('name', 'Unknown Project') if project else 'Unknown Project',
            "employee_id": employee_id,
            "employee_name": employee.get('name', 'Unassigned') if employee else 'Unassigned',
            "employee_phone": employee.get('phone', '') if employee else '',
            "priority": priority,
            "reason": reason,
            "due_date": task.get('due_date', ''),
            "hours_since_update": hours_since,
            "status": task.get('status', 'ready_to_start')
        }
        
    except Exception as e:
        print(f"⚠️ Error enriching task: {e}")
        return None


# Test function
if __name__ == "__main__":
    print("\n🧪 Testing attention service...")
    print("=" * 60)
    
    items = get_attention_items()
    print(f"\nFound {len(items)} attention items:")
    for item in items[:5]:  # Show first 5
        print(f"\n  [{item['priority'].upper()}] {item['task_title']}")
        print(f"    Reason: {item['reason']}")
        print(f"    Employee: {item['employee_name']}")
        print(f"    Project: {item['project_name']}")
    
    print("\n✅ Attention service test complete!")
