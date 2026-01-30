"""
Tasks API Blueprint
Handles all task-related API endpoints.
"""

from flask import Blueprint, jsonify, request
import db.tasks
import db.activities

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
        
        # Convert phone number to employee_id if assignedTo is a string (phone)
        if data.get('assignedTo') and isinstance(data['assignedTo'], str):
            phone = data['assignedTo']
            employee_result = db.employees.get_employee_by_phone(phone)
            if employee_result['success'] and employee_result.get('data'):
                data['assignedTo'] = employee_result['data']['id']
            else:
                # If employee not found by phone, try as-is (might be employee_id already)
                pass
        
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


@tasks_bp.route('/tasks/<task_id>/activities', methods=['GET'])
def get_task_activities(task_id):
    """
    Get all activities for a task.
    
    Returns activities in chronological order with attachments.
    
    Returns:
        JSON response with list of activities
    """
    try:
        print(f"📥 GET /api/tasks/{task_id}/activities - Fetching activities")
        
        # Verify task exists
        task_result = db.tasks.get_task_by_id(task_id)
        if not task_result['success']:
            return jsonify({
                "success": False,
                "error": "Task not found"
            }), 404
        
        # Get activities
        activities_result = db.activities.get_activities_by_task(task_id)
        
        if not activities_result['success']:
            return jsonify(activities_result), 500
        
        print(f"✅ Found {len(activities_result['data'])} activities for task {task_id}")
        return jsonify(activities_result), 200
        
    except Exception as e:
        print(f"❌ Error in get_task_activities endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch activities"
        }), 500


@tasks_bp.route('/tasks/<task_id>/activities', methods=['POST'])
def create_task_activity(task_id):
    """
    Create a new activity (comment) for a task.
    
    Processes @mentions and sends WhatsApp notifications.
    
    Request body:
        {
            "authorType": "admin|employee|system",
            "authorId": 1,
            "authorName": "John Doe",
            "activityType": "comment",
            "source": "web_dashboard",
            "message": "Comment with @mention"
        }
    
    Returns:
        JSON response with created activity
    """
    try:
        data = request.get_json()
        
        print(f"📥 POST /api/tasks/{task_id}/activities - Creating activity")
        
        # Verify task exists
        task_result = db.tasks.get_task_by_id(task_id)
        if not task_result['success']:
            return jsonify({
                "success": False,
                "error": "Task not found"
            }), 404
        
        # Validate required fields
        required_fields = ['authorType', 'activityType', 'source', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Create activity data
        activity_data = {
            'task_id': task_id,
            'author_type': data['authorType'],
            'author_id': data.get('authorId'),
            'author_name': data.get('authorName', 'Unknown'),
            'activity_type': data['activityType'],
            'source': data['source'],
            'message': data['message']
        }
        
        # Create activity
        activity_result = db.activities.create_activity(activity_data)
        
        if not activity_result['success']:
            return jsonify(activity_result), 500
        
        activity_id = activity_result['data']['id']
        print(f"✅ Created activity {activity_id} for task {task_id}")
        
        # Process @mentions
        if data.get('message'):
            import services.mention_service as mention_service
            
            mention_result = mention_service.process_mentions_in_comment(
                task_id=task_id,
                activity_id=activity_id,
                comment_text=data['message'],
                author_name=data.get('authorName', 'Someone')
            )
            
            print(f"📢 Mention processing: {mention_result['mentions_found']} found, {mention_result['notifications_sent']} sent")
        
        return jsonify({
            "success": True,
            "data": activity_result['data']
        }), 201
        
    except Exception as e:
        print(f"❌ Error in create_task_activity endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Failed to create activity"
        }), 500

