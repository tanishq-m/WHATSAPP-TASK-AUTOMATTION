"""
Webhooks API Blueprint
Handles incoming webhook requests from external services (e.g., Kapso for WhatsApp).
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import db.tasks
import services.kapso_service as kapso_service

# Create Blueprint
webhooks_bp = Blueprint('webhooks', __name__)


# ============================================================================
# WEBHOOK ENDPOINTS (For receiving WhatsApp responses)
# ============================================================================

@webhooks_bp.route('/webhook/whatsapp', methods=['POST'])
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
        existing_task_result = db.tasks.get_task_by_id(task_id)
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
        
        result = db.tasks.update_task(task_id, update_data)
        
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


@webhooks_bp.route('/webhook/whatsapp', methods=['GET'])
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
