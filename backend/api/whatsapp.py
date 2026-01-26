"""
WhatsApp Integration API Blueprint
Handles all WhatsApp-related API endpoints for sending messages.
"""

from flask import Blueprint, jsonify, request
import db.tasks
import db.employees
import services.kapso_service as kapso_service

# Create Blueprint
whatsapp_bp = Blueprint('whatsapp', __name__)


# ============================================================================
# WHATSAPP INTEGRATION ENDPOINTS
# ============================================================================

@whatsapp_bp.route('/tasks/<task_id>/send-whatsapp', methods=['POST'])
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
        task_result = db.tasks.get_task_by_id(task_id)
        
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
        employee_result = db.employees.get_employee_by_id(task['employee_id'])
        
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
            # Update task to mark WhatsApp as sent (use camelCase for db.tasks.update_task)
            db.tasks.update_task(task_id, {'whatsappSent': 1})
            
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


@whatsapp_bp.route('/tasks/<task_id>/send-whatsapp-buttons', methods=['POST'])
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
        task_result = db.tasks.get_task_by_id(task_id)
        
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
        employee_result = db.employees.get_employee_by_id(task['employee_id'])
        
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
            db.tasks.update_task(task_id, {'whatsappSent': 1})
            
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


@whatsapp_bp.route('/tasks/<task_id>/whatsapp-status', methods=['GET'])
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
        task_result = db.tasks.get_task_by_id(task_id)
        
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
