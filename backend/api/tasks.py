"""
Tasks API Blueprint
Handles all task-related API endpoints.
"""

from flask import Blueprint, jsonify, request
import db.tasks

# Create Blueprint
tasks_bp = Blueprint('tasks', __name__)


# ============================================================================
# TASK ENDPOINTS
# ============================================================================

@tasks_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """
    Get all tasks, optionally filtered by project.
    
    Query params:
        projectId (optional): Filter tasks by project ID
        
    Returns:
        JSON response with list of tasks
    """
    try:
        project_id = request.args.get('projectId')
        print(f"📥 GET /api/tasks - Fetching tasks{f' for project {project_id}' if project_id else ''}")
        
        result = db.tasks.get_all_tasks(project_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ Error in get_tasks endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch tasks"
        }), 500


@tasks_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """
    Get a single task by ID.
    
    Args:
        task_id: Task ID
        
    Returns:
        JSON response with task data
    """
    try:
        print(f"📥 GET /api/tasks/{task_id} - Fetching task")
        result = db.tasks.get_task_by_id(task_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"❌ Error in get_task endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch task"
        }), 500


@tasks_bp.route('/tasks', methods=['POST'])
def create_task():
    """
    Create a new task.
    
    Body:
        {
            "title": "Task title",
            "description": "Task description",
            "projectId": "proj_001",
            "assignedTo": 1,
            "dueDate": "2025-01-30",
            "priority": "high",
            "status": "ready_to_start"
        }
        
    Returns:
        JSON response with created task
    """
    try:
        data = request.get_json()
        print(f"📥 POST /api/tasks - Creating task: {data.get('title')}")
        
        # Validate required fields (assignedTo is optional - tasks can be unassigned)
        required_fields = ['title', 'projectId']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Set defaults for optional fields
        data.setdefault('assignedTo', None)
        data.setdefault('dueDate', None)
        data.setdefault('priority', 'medium')
        data.setdefault('status', 'unassigned')
        
        result = db.tasks.create_task(data)
        
        if result['success']:
            print(f"✅ Created task: {result['data']['task_id']}")
            return jsonify(result), 201
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ Error in create_task endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to create task"
        }), 500


@tasks_bp.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """
    Update a task.
    
    ⚠️ UPDATE SOURCE SEPARATION (Issue #8):
    This endpoint handles TWO distinct update flows:
    
    1. ADMIN UPDATES (source: 'admin'):
       - Triggered by admin drag-and-drop on Kanban board
       - Admin can freely move tasks between ANY columns
       - NO WhatsApp messages are sent (admin action only)
       - Status updates are immediate and unrestricted
       
    2. WEBHOOK UPDATES (source: 'webhook'):
       - Triggered by employee button clicks in WhatsApp
       - Handled separately via /api/webhook/whatsapp endpoint
       - Auto-moves task to appropriate column based on response
       - Sends confirmation message back to employee
    
    The separation is maintained by:
    - Admin updates: Explicitly pass 'updateSource: admin' from frontend
    - Webhook updates: Use separate endpoint /api/webhook/whatsapp
    - This endpoint does NOT send WhatsApp messages (admin actions only)
    
    Args:
        task_id: Task ID
        
    Body (all fields optional):
        {
            "title": "Updated title",
            "description": "Updated description",
            "assignedTo": 2,
            "dueDate": "2025-02-15",
            "priority": "medium",
            "status": "in_progress",
            "updateSource": "admin"  // Optional: 'admin' or 'webhook'
        }
        
    Returns:
        JSON response with updated task
    """
    try:
        data = request.get_json()
        update_source = data.get('updateSource', 'unknown')
        print(f"📥 PUT /api/tasks/{task_id} - Updating task (source: {update_source})")
        
        result = db.tasks.update_task(task_id, data)
        
        if result['success']:
            print(f"✅ Updated task: {task_id}")
            return jsonify(result), 200
        else:
            return jsonify(result), 404 if 'not found' in result.get('error', '').lower() else 500
            
    except Exception as e:
        print(f"❌ Error in update_task endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to update task"
        }), 500


@tasks_bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """
    Delete a task.
    
    Args:
        task_id: Task ID
        
    Returns:
        JSON response with success message
    """
    try:
        print(f"📥 DELETE /api/tasks/{task_id} - Deleting task")
        
        result = db.tasks.delete_task(task_id)
        
        if result['success']:
            print(f"✅ Deleted task: {task_id}")
            return jsonify(result), 200
        elif result.get('not_found'):
            return jsonify(result), 404
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ Error in delete_task endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to delete task"
        }), 500
