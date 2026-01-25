"""
WhatsApp Task Manager - Flask Backend
Main application file for the task management API.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os
from config import FLASK_ENV, PORT, DEBUG, ALLOWED_ORIGINS
import database  # Import database module (auto-initializes DB)
import kapso_service  # Import Kapso WhatsApp service

# Initialize Flask app
app = Flask(__name__)

# Configure CORS to allow requests from React frontend
CORS(app, resources={
    r"/api/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configure Flask app
app.config['ENV'] = FLASK_ENV
app.config['DEBUG'] = DEBUG

print("=" * 60)
print("🚀 WhatsApp Task Manager - Flask Backend Starting...")
print("=" * 60)
print(f"Environment: {FLASK_ENV}")
print(f"Debug Mode: {DEBUG}")
print(f"Port: {PORT}")
print(f"Allowed Origins: {ALLOWED_ORIGINS}")
print("=" * 60)


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        JSON response with status and database connectivity
    
    Example:
        GET /api/health
        Response: {"status": "healthy", "database": "connected", "timestamp": "..."}
    """
    try:
        print("✅ Health check endpoint called")
        
        # Check database connectivity
        db_status = "connected"
        try:
            import sqlite3
            conn = sqlite3.connect(database.DATABASE_PATH)
            conn.execute("SELECT 1")
            conn.close()
        except Exception as db_error:
            db_status = f"error: {str(db_error)}"
        
        return jsonify({
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.now().isoformat(),
            "environment": FLASK_ENV
        }), 200
    except Exception as e:
        print(f"❌ Error in health check: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============================================================================
# EMPLOYEE ENDPOINTS
# ============================================================================

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """
    Get all employees from the database.
    
    Returns:
        JSON response with list of employees
        
    Example:
        GET /api/employees
        Response: {
            "success": true,
            "data": [
                {"id": 1, "name": "Rajesh Kumar", "phone": "+919876543210", ...},
                ...
            ]
        }
    """
    try:
        print("📥 GET /api/employees - Fetching all employees")
        result = database.get_all_employees()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ Error in get_employees endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch employees"
        }), 500


@app.route('/api/employees/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    """
    Get a single employee by ID.
    
    Args:
        employee_id: Employee ID from URL
        
    Returns:
        JSON response with employee data
        
    Example:
        GET /api/employees/1
        Response: {"success": true, "data": {...}}
    """
    try:
        print(f"📥 GET /api/employees/{employee_id} - Fetching employee")
        result = database.get_employee_by_id(employee_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"❌ Error in get_employee endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch employee"
        }), 500


# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """
    Get all projects from the database.
    
    Returns:
        JSON response with list of projects
        
    Example:
        GET /api/projects
        Response: {"success": true, "data": [...]}
    """
    try:
        print("📥 GET /api/projects - Fetching all projects")
        result = database.get_all_projects()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ Error in get_projects endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch projects"
        }), 500


@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """
    Get a single project by ID with assigned employees.
    
    Args:
        project_id: Project ID from URL
        
    Returns:
        JSON response with project data
    """
    try:
        print(f"📥 GET /api/projects/{project_id} - Fetching project")
        result = database.get_project_by_id(project_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"❌ Error in get_project endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch project"
        }), 500


@app.route('/api/projects', methods=['POST'])
def create_project():
    """
    Create a new project.
    
    Body:
        {
            "name": "Project Name",
            "startDate": "2025-01-01",
            "endDate": "2025-03-31",
            "employeeIds": [1, 2, 3],
            "color": "#3B82F6"
        }
        
    Returns:
        JSON response with created project
    """
    try:
        print("📥 POST /api/projects - Creating project")
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({
                "success": False,
                "error": "Project name is required"
            }), 400
        
        # Generate project ID (e.g., proj_001)
        import random
        project_id = f"proj_{random.randint(100, 999)}"
        
        # Prepare project data
        # Accept both 'employeeIds' and 'assignedEmployees' from frontend
        employee_ids = data.get('employeeIds') or data.get('assignedEmployees', [])
        project_data = {
            'id': project_id,
            'name': data['name'],
            'startDate': data.get('startDate', ''),
            'endDate': data.get('endDate', ''),
            'color': data.get('color', '#3B82F6'),
            'assignedEmployees': employee_ids
        }
        
        result = database.create_project(project_data)
        
        if result['success']:
            print(f"✅ Project created: {project_id}")
            return jsonify(result), 201
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ Error in create_project endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to create project"
        }), 500


@app.route('/api/projects/<project_id>', methods=['PUT'])
def update_project_endpoint(project_id):
    """
    Update an existing project.
    
    Args:
        project_id: Project ID from URL
        
    Body:
        {
            "name": "Updated Name",
            "startDate": "2025-01-01",
            "endDate": "2025-03-31",
            "employeeIds": [1, 2],
            "color": "#3B82F6"
        }
        
    Returns:
        JSON response with updated project
    """
    try:
        print(f"📥 PUT /api/projects/{project_id} - Updating project")
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        result = database.update_project(project_id, data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ Error in update_project endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to update project"
        }), 500


@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project_endpoint(project_id):
    """
    Delete a project and all its tasks.
    
    Args:
        project_id: Project ID from URL
        
    Returns:
        JSON response with success message
    """
    try:
        print(f"📥 DELETE /api/projects/{project_id} - Deleting project")
        result = database.delete_project(project_id)
        
        if result['success']:
            return jsonify(result), 200
        elif result.get('not_found'):
            return jsonify(result), 404
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ Error in delete_project endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to delete project"
        }), 500



# ============================================================================
# TASK ENDPOINTS
# ============================================================================

@app.route('/api/tasks', methods=['GET'])
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
        
        result = database.get_all_tasks(project_id)
        
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


@app.route('/api/tasks/<task_id>', methods=['GET'])
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
        result = database.get_task_by_id(task_id)
        
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


@app.route('/api/tasks', methods=['POST'])
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
        data.setdefault('status', 'todo')
        
        result = database.create_task(data)
        
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


@app.route('/api/tasks/<task_id>', methods=['PUT'])
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
        
        result = database.update_task(task_id, data)
        
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


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
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
        
        result = database.delete_task(task_id)
        
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


# ============================================================================
# WHATSAPP INTEGRATION ENDPOINTS
# ============================================================================

@app.route('/api/tasks/<task_id>/send-whatsapp', methods=['POST'])
def send_task_to_whatsapp(task_id):
    """
    Send a task assignment message to employee via WhatsApp.
    
    Args:
        task_id: Task ID to send
        
    Returns:
        JSON response with success status
        
    Example:
        POST /api/tasks/task_001/send-whatsapp
        Response: {"success": true, "message": "Task sent to WhatsApp"}
    """
    try:
        print(f"📥 POST /api/tasks/{task_id}/send-whatsapp - Sending task to WhatsApp")
        
        # Get task from database
        task_result = database.get_task_by_id(task_id)
        
        if not task_result or not task_result.get('success'):
            print(f"❌ Task not found: {task_id}")
            return jsonify({
                "success": False,
                "error": "Task not found"
            }), 404
        
        task = task_result['data']
        
        # Check if task has an assigned employee
        if not task.get('employee_id'):
            print(f"❌ Task {task_id} has no assigned employee")
            return jsonify({
                "success": False,
                "error": "Task has no assigned employee"
            }), 400
        
        # Get employee details
        employee_result = database.get_employee_by_id(task['employee_id'])
        
        if not employee_result or not employee_result.get('success'):
            print(f"❌ Employee not found: {task['employee_id']}")
            return jsonify({
                "success": False,
                "error": "Employee not found"
            }), 404
        
        employee = employee_result['data']
        
        # Prepare task data for WhatsApp message
        task_data = {
            "task_id": task['task_id'],
            "title": task['title'],
            "description": task['description'],
            "due_date": task['due_date'],
            "priority": task['priority'],
            "employee_name": employee['name']
        }
        
        # Remove + sign from phone number if present
        employee_phone = employee['phone'].replace('+', '')
        
        # Send WhatsApp message via Kapso
        result = kapso_service.send_task_assignment(employee_phone, task_data)
        
        if result['success']:
            # Update task to mark WhatsApp as sent
            database.update_task(task_id, {'whatsapp_sent': 1})
            
            print(f"✅ Task {task_id} sent to WhatsApp successfully")
            return jsonify({
                "success": True,
                "message": f"Task sent to {employee['name']} via WhatsApp"
            }), 200
        else:
            print(f"❌ Failed to send task to WhatsApp: {result.get('error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to send WhatsApp message')
            }), 500
            
    except Exception as e:
        print(f"❌ Error in send_task_to_whatsapp endpoint: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/tasks/<task_id>/send-whatsapp-buttons', methods=['POST'])
def send_task_with_buttons(task_id):
    """
    Send a task with interactive Yes/No buttons to employee via WhatsApp.
    This allows collecting task completion status directly from WhatsApp.
    
    Args:
        task_id: Task ID to send
        
    Returns:
        JSON response with success status
        
    Example:
        POST /api/tasks/task_001/send-whatsapp-buttons
        Response: {"success": true, "message": "Task sent with status buttons"}
    """
    try:
        print(f"📥 POST /api/tasks/{task_id}/send-whatsapp-buttons - Sending task with buttons")
        
        # Get task from database
        task_result = database.get_task_by_id(task_id)
        
        if not task_result or not task_result.get('success'):
            print(f"❌ Task not found: {task_id}")
            return jsonify({
                "success": False,
                "error": "Task not found"
            }), 404
        
        task = task_result['data']
        
        # Check if task has an assigned employee
        if not task.get('employee_id'):
            print(f"❌ Task {task_id} has no assigned employee")
            return jsonify({
                "success": False,
                "error": "Task has no assigned employee"
            }), 400
        
        # Get employee details
        employee_result = database.get_employee_by_id(task['employee_id'])
        
        if not employee_result or not employee_result.get('success'):
            print(f"❌ Employee not found: {task['employee_id']}")
            return jsonify({
                "success": False,
                "error": "Employee not found"
            }), 404
        
        employee = employee_result['data']
        
        # Prepare task data for WhatsApp message
        task_data = {
            "task_id": task['task_id'],
            "title": task['title'],
            "description": task['description'],
            "due_date": task['due_date'],
            "priority": task['priority'],
            "employee_name": employee['name']
        }
        
        # Remove + sign from phone number if present
        employee_phone = employee['phone'].replace('+', '')
        
        # Send WhatsApp message with interactive buttons via Kapso
        result = kapso_service.send_task_with_status_request(employee_phone, task_data)
        
        if result['success']:
            # Update task to mark WhatsApp as sent
            database.update_task(task_id, {'whatsappSent': 1})
            
            print(f"✅ Task {task_id} sent with buttons to WhatsApp successfully")
            return jsonify({
                "success": True,
                "message": f"Task sent to {employee['name']} via WhatsApp with status buttons"
            }), 200
        else:
            print(f"❌ Failed to send task with buttons to WhatsApp: {result.get('error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to send WhatsApp message')
            }), 500
            
    except Exception as e:
        print(f"❌ Error in send_task_with_buttons endpoint: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# WEBHOOK ENDPOINTS (For receiving WhatsApp responses)
# ============================================================================

@app.route('/', methods=['POST'])
@app.route('/api/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    Webhook endpoint to receive WhatsApp message responses from Kapso.
    
    NOTE: Kapso sends webhooks to the root path '/', so we handle both:
    - POST / (Kapso default)
    - POST /api/webhook/whatsapp (explicit endpoint)
    
    This handles button clicks from interactive messages sent to employees.
    When an employee clicks "Yes, Completed" or "No, Not Yet", Kapso sends
    a webhook with the button ID and message details.
    
    Per Issue #3 workflow:
    - "Yes, Completed" → Move task to 'pending_verification' status
    - "No, Not Yet" → Keep task in 'in_progress' status
    
    Kapso webhook payload structure:
    {
        "message": {
            "from": "918005800336",
            "interactive": {
                "type": "button_reply",
                "button_reply": {
                    "id": "completed_task_015",
                    "title": "✅ Yes, Completed"
                }
            }
        },
        "conversation": {...}
    }
    """
    try:
        # Get raw payload
        payload = request.get_json()
        
        print(f"\n📥 WEBHOOK RECEIVED")
        print(f"📦 Headers: {dict(request.headers)}")
        print(f"📦 Payload: {payload}")
        
        # Acknowledge receipt immediately (Kapso expects 200 OK)
        
        # Check event type from header (Kapso uses X-Webhook-Event header)
        event_type = request.headers.get('X-Webhook-Event', '')
        
        if event_type and event_type != 'whatsapp.message.received':
            print(f"ℹ️ Ignoring event type: {event_type}")
            return jsonify({"status": "ignored", "reason": f"Event type: {event_type}"}), 200
        
        # Extract message data (Kapso sends directly, not wrapped in 'data')
        message = payload.get('message', {})
        
        # Check if this is an interactive button reply
        interactive = message.get('interactive', {})
        interactive_type = interactive.get('type', '')
        
        # Get button reply data
        button_reply = interactive.get('button_reply', {})
        reply_option_id = button_reply.get('id', '')
        reply_option_title = button_reply.get('title', '')
        
        # Get phone number from message
        phone_number = message.get('from', '')
        
        print(f"📱 From: {phone_number}")
        print(f"🔘 Interactive Type: {interactive_type}")
        print(f"🆔 Button ID: {reply_option_id}")
        print(f"📝 Button Title: {reply_option_title}")
        
        # Only process button replies
        if interactive_type != 'button_reply':
            print(f"ℹ️ Not a button reply, ignoring")
            return jsonify({"status": "ignored", "reason": "Not a button reply"}), 200
        
        # Parse the button ID to extract task_id and action
        # Format: "completed_task_001" or "not_completed_task_001"
        if reply_option_id.startswith('completed_'):
            task_id = reply_option_id.replace('completed_', '')
            response_status = 'completed'
            new_task_status = 'pending_verification'  # Move to pending verification for admin review
        elif reply_option_id.startswith('not_completed_'):
            task_id = reply_option_id.replace('not_completed_', '')
            response_status = 'not_completed'
            new_task_status = 'in_progress'  # Keep in progress
        else:
            print(f"⚠️ Unknown button ID format: {reply_option_id}")
            return jsonify({"status": "ignored", "reason": "Unknown button ID"}), 200
        
        print(f"🎯 Task ID: {task_id}")
        print(f"📊 Response: {response_status}")
        print(f"📍 New Status: {new_task_status}")
        
        # ============================================================================
        # DUPLICATE RESPONSE PREVENTION
        # Check if task already has a WhatsApp response to prevent multiple submissions
        # ============================================================================
        existing_task_result = database.get_task_by_id(task_id)
        if existing_task_result['success'] and existing_task_result['data']:
            existing_task = existing_task_result['data']
            existing_response = existing_task.get('whatsapp_response')
            
            if existing_response:
                # Task already has a response - ignore this duplicate click
                print(f"⚠️ Task {task_id} already has response: {existing_response}")
                print(f"🚫 Ignoring duplicate button click")
                
                # Send informative message to employee
                clean_phone = phone_number.replace('+', '')
                
                response_emoji = '✅ Completed' if existing_response == 'completed' else '❌ Not Yet'
                warning_msg = (
                    f"⚠️ You already responded to this task.\n\n"
                    f"Your original response: {response_emoji}\n\n"
                    f"Your first response has been kept. "
                    f"If you need to change it, please contact your manager."
                )
                
                # Send warning (best effort)
                try:
                    kapso_service.send_text_message(clean_phone, warning_msg)
                    print(f"✅ Duplicate response warning sent to {clean_phone}")
                except Exception as e:
                    print(f"⚠️ Could not send duplicate response warning: {e}")
                
                return jsonify({
                    "status": "ignored",
                    "reason": "Task already has a response",
                    "task_id": task_id,
                    "original_response": existing_response,
                    "attempted_response": response_status
                }), 200
        
        # ============================================================================
        # PROCESS NEW RESPONSE
        # First time response - update task in database
        # ============================================================================
        update_data = {
            'whatsappResponse': response_status,
            'responseNotes': f"Employee clicked: {reply_option_title} at {datetime.now().isoformat()}",
            'status': new_task_status,  # Always update status based on response
            'updateSource': 'webhook'  # Mark as webhook update (Issue #8)
        }
        
        result = database.update_task(task_id, update_data)
        
        if result['success']:
            print(f"✅ Task {task_id} updated with WhatsApp response: {response_status}")
            print(f"📦 Task moved to status: {new_task_status}")
            
            # Send confirmation message to employee
            # Clean phone number
            clean_phone = phone_number.replace('+', '')
            
            if response_status == 'completed':
                confirm_msg = f"✅ Great job! Your task has been marked as completed and is now pending verification by your manager. Thank you!"
            else:
                confirm_msg = f"📝 Got it! Your task will remain in progress. Let us know when you're done!"
            
            # Send confirmation (best effort, don't fail webhook if this fails)
            try:
                kapso_service.send_text_message(clean_phone, confirm_msg)
                print(f"✅ Confirmation message sent to {clean_phone}")
            except Exception as e:
                print(f"⚠️ Could not send confirmation: {e}")
            
            return jsonify({
                "status": "processed",
                "task_id": task_id,
                "response": response_status,
                "task_updated": True
            }), 200
        else:
            print(f"❌ Failed to update task: {result.get('error')}")
            return jsonify({
                "status": "error",
                "error": result.get('error', 'Failed to update task')
            }), 200  # Still return 200 to Kapso to prevent retries
            
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        # Return 200 anyway to prevent Kapso from retrying
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 200


@app.route('/api/webhook/whatsapp', methods=['GET'])
def whatsapp_webhook_verify():
    """
    Webhook verification endpoint (GET request).
    Some webhook providers send GET to verify the endpoint exists.
    """
    return jsonify({
        "status": "ok",
        "message": "WhatsApp webhook endpoint is active",
        "supported_events": ["whatsapp.message.received"]
    }), 200


# ============================================================================
# TASK WHATSAPP STATUS ENDPOINT
# ============================================================================

@app.route('/api/tasks/<task_id>/whatsapp-status', methods=['GET'])
def get_task_whatsapp_status(task_id):
    """
    Get the WhatsApp status for a specific task.
    Returns whether message was sent and if a response was received.
    
    Example:
        GET /api/tasks/task_001/whatsapp-status
        Response: {
            "success": true,
            "data": {
                "task_id": "task_001",
                "whatsapp_sent": true,
                "whatsapp_response": "completed",
                "response_notes": "Employee clicked: ✅ Yes, Completed at 2025-01-20T10:30:00"
            }
        }
    """
    try:
        task_result = database.get_task_by_id(task_id)
        
        if not task_result or not task_result.get('success'):
            return jsonify({
                "success": False,
                "error": "Task not found"
            }), 404
        
        task = task_result['data']
        
        return jsonify({
            "success": True,
            "data": {
                "task_id": task['task_id'],
                "whatsapp_sent": bool(task.get('whatsapp_sent')),
                "whatsapp_response": task.get('whatsapp_response'),
                "response_notes": task.get('response_notes')
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting WhatsApp status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    print(f"❌ 404 Error: {request.url}")
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "path": request.path
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    print(f"❌ 500 Error: {error}")
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors."""
    print(f"❌ 400 Error: {error}")
    return jsonify({
        "success": False,
        "error": "Bad request"
    }), 400


# ============================================================================
# REQUEST LOGGING (for debugging)
# ============================================================================

@app.before_request
def log_request():
    """Log all incoming requests for debugging."""
    print(f"📥 {request.method} {request.path}")
    if request.method in ['POST', 'PUT'] and request.is_json:
        print(f"   Body: {request.get_json()}")


@app.after_request
def log_response(response):
    """Log all outgoing responses for debugging."""
    print(f"📤 {request.method} {request.path} → Status: {response.status_code}")
    return response


# ============================================================================
# RUN THE APP
# ============================================================================

if __name__ == '__main__':
    print("\n✅ Flask server is ready!")
    print(f"🌐 API running at: http://localhost:{PORT}/api")
    print(f"🏥 Health check: http://localhost:{PORT}/api/health")
    print("\n💡 Press Ctrl+C to stop the server\n")
    
    # Run the Flask development server
    app.run(
        host='0.0.0.0',  # Allow connections from any IP (for testing)
        port=PORT,
        debug=DEBUG,
        use_reloader=True  # Auto-reload on code changes
    )
