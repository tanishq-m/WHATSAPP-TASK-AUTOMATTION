"""
Webhooks API Blueprint
Handles incoming webhook requests from external services (e.g., Kapso for WhatsApp).
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import db.tasks
import db.employees
import db.activities
import services.kapso_service as kapso_service
import config

# Create Blueprint
webhooks_bp = Blueprint('webhooks', __name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def handle_media_reply(message_data, phone_number):
    """
    Handle media message replies (image, video, document, audio).
    Downloads media, creates activity and attachment records.
    """
    try:
        # Get message context (reply information)
        context = message_data.get('context', {})
        replied_to_msg_id = context.get('id')
        message_type = message_data.get('type', '')
        
        print(f"📎 Media message type: {message_type}")
        print(f"🔗 Reply to message ID: {replied_to_msg_id}")
        
        # Extract media information based on type
        media_info = message_data.get(message_type, {})
        media_id = media_info.get('id')
        caption = media_info.get('caption', '')
        
        # Get Kapso media info
        kapso_data = message_data.get('kapso', {})
        media_url = kapso_data.get('media_url')
        media_data = kapso_data.get('media_data', {})
        filename = media_data.get('filename', f'media_{media_id}')
        content_type = media_data.get('content_type', f'{message_type}/unknown')
        
        print(f"📁 Filename: {filename}")
        print(f"📋 Content Type: {content_type}")
        print(f"🔗 Media URL: {media_url}")
        
        if not media_url:
            print("❌ No media URL provided")
            return None
        
        # Check if this is a reply to a tracked task message
        if replied_to_msg_id:
            # Look up task by WhatsApp message ID
            task_lookup = db.activities.get_task_by_whatsapp_message_id(replied_to_msg_id)
            
            if task_lookup['success']:
                task_id = task_lookup['data']['task_id']
                employee_phone = task_lookup['data']['employee_phone']
                
                print(f"✅ Found task {task_id} for media reply")
                
                # Get employee info
                employee_result = db.employees.get_employee_by_phone(employee_phone)
                if not employee_result['success']:
                    print(f"⚠️ Employee not found for phone {employee_phone}")
                    return None
                
                employee = employee_result['data']
                
                # Download media file
                try:
                    import requests
                    import os
                    import uuid
                    
                    # Create upload directory
                    upload_dir = f"uploads/{task_id}"
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Generate unique filename
                    file_ext = filename.split('.')[-1] if '.' in filename else ''
                    unique_filename = f"{uuid.uuid4().hex}.{file_ext}" if file_ext else uuid.uuid4().hex
                    file_path = f"{upload_dir}/{unique_filename}"
                    
                    # Download file
                    response = requests.get(media_url)
                    response.raise_for_status()
                    
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    file_size = len(response.content)
                    print(f"✅ Downloaded media: {file_path} ({file_size} bytes)")
                    
                except Exception as e:
                    print(f"❌ Failed to download media: {e}")
                    return None
                
                # Create activity for the attachment
                activity_data = {
                    'task_id': task_id,
                    'author_type': 'employee',
                    'author_id': employee['id'],
                    'author_name': employee['name'],
                    'activity_type': 'attachment',
                    'source': 'whatsapp_reply',
                    'message': f"Shared {filename}" + (f": {caption}" if caption else ""),
                    'whatsapp_message_id': message_data.get('id')
                }
                
                activity_result = db.activities.create_activity(activity_data)
                
                if activity_result['success']:
                    activity_id = activity_result['data']['id']
                    
                    # Create attachment record
                    # Map message type to media type
                    media_type_map = {
                        'image': 'image',
                        'video': 'video', 
                        'document': 'document',
                        'audio': 'audio'
                    }
                    
                    attachment_data = {
                        'activity_id': activity_id,
                        'task_id': task_id,
                        'media_type': media_type_map.get(message_type, 'document'),
                        'file_path': file_path,
                        'filename': filename,
                        'content_type': content_type,
                        'file_size': file_size
                    }
                    
                    attachment_result = db.activities.create_attachment(attachment_data)
                    
                    if attachment_result['success']:
                        print(f"✅ Created attachment record for {filename}")
                        return {
                            'status': 'processed',
                            'task_id': task_id,
                            'media_saved': True,
                            'filename': filename
                        }
                    else:
                        print(f"❌ Failed to create attachment record: {attachment_result.get('error')}")
                else:
                    print(f"❌ Failed to create activity: {activity_result.get('error')}")
            else:
                print(f"ℹ️ Media message not linked to tracked task")
                # Could implement unlinked media handling here
        else:
            print(f"ℹ️ Media message without reply context")
        
        return None
        
    except Exception as e:
        print(f"❌ Error handling media reply: {e}")
        import traceback
        traceback.print_exc()
        return None


def handle_text_reply(message_data, phone_number):
    """
    Handle regular text message replies (not button clicks).
    Checks if message is a reply to a tracked task message,
    creates activity, and sends form URL if requested.
    """
    try:
        # Get message context (reply information)
        context = message_data.get('context', {})
        replied_to_msg_id = context.get('id')  # WhatsApp message ID being replied to
        
        # Get message text
        text_data = message_data.get('text', {})
        message_body = text_data.get('body', '').strip()
        
        if not message_body:
            print("ℹ️ Empty message body, ignoring")
            return None
        
        print(f"💬 Text message: {message_body}")
        print(f"🔗 Reply to message ID: {replied_to_msg_id}")
        
        # Check if this is a reply to a tracked task message
        if replied_to_msg_id:
            # Look up task by WhatsApp message ID
            task_lookup = db.activities.get_task_by_whatsapp_message_id(replied_to_msg_id)
            
            if task_lookup['success']:
                task_id = task_lookup['data']['task_id']
                employee_phone = task_lookup['data']['employee_phone']
                
                print(f"✅ Found task {task_id} for message thread")
                
                # Get employee info
                employee_result = db.employees.get_employee_by_phone(employee_phone)
                if not employee_result['success']:
                    print(f"⚠️ Employee not found for phone {employee_phone}")
                    return None
                
                employee = employee_result['data']
                
                # Create activity for this reply
                activity_data = {
                    'task_id': task_id,
                    'author_type': 'employee',
                    'author_id': employee['id'],
                    'author_name': employee['name'],
                    'activity_type': 'comment',
                    'source': 'whatsapp_reply',
                    'message': message_body
                }
                
                activity_result = db.activities.create_activity(activity_data)
                
                if activity_result['success']:
                    print(f"✅ Created activity from WhatsApp reply")
                    
                    # Check if user is requesting form
                    message_lower = message_body.lower()
                    if any(keyword in message_lower for keyword in ['form', 'link', 'submit', 'url', 'help']):
                        # Generate submission token and send form URL
                        token_result = db.activities.create_submission_token(task_id, employee['id'])
                        
                        if token_result['success']:
                            token = token_result['data']['token']
                            form_url = f"{config.FRONTEND_URL}/submit/{token}"
                            
                            # Get task details for message
                            task_result = db.tasks.get_task_by_id(task_id)
                            task_title = task_result['data']['title'] if task_result['success'] else 'your task'
                            
                            form_message = (
                                f"📝 Here's your submission form for *{task_title}*:\n\n"
                                f"{form_url}\n\n"
                                f"You can add comments and attach photos/documents.\n"
                                f"⚠️ This link can only be used once."
                            )
                            
                            clean_phone = phone_number.replace('+', '')
                            kapso_service.send_text_message(clean_phone, form_message)
                            print(f"✅ Sent form URL to {clean_phone}")
                    
                    return {
                        'status': 'processed',
                        'task_id': task_id,
                        'activity_created': True
                    }
                else:
                    print(f"❌ Failed to create activity: {activity_result.get('error')}")
                    return None
            else:
                print(f"ℹ️ Message not linked to a tracked task")
        
        # Check if this is an unthreaded message requesting help
        message_lower = message_body.lower()
        if any(keyword in message_lower for keyword in ['help', 'task', 'form', 'submit']):
            # Send general help message
            help_msg = (
                "👋 Hello! I'm your task manager assistant.\n\n"
                "To update a task:\n"
                "1️⃣ Reply directly to the task message I sent you\n"
                "2️⃣ Type 'form' or 'link' to get a submission form\n\n"
                "Or just reply with your update!"
            )
            clean_phone = phone_number.replace('+', '')
            kapso_service.send_text_message(clean_phone, help_msg)
            print(f"✅ Sent help message to {clean_phone}")
            
            return {
                'status': 'processed',
                'help_sent': True
            }
        
        # Untracked text message
        print(f"ℹ️ Untracked text message, ignoring")
        return None
        
    except Exception as e:
        print(f"❌ Error handling text reply: {e}")
        import traceback
        traceback.print_exc()
        return None


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
        
        # Check message type
        message_type = message.get('type', '')
        
        print(f"📱 From: {message.get('from', '')}")
        print(f"📋 Message Type: {message_type}")
        
        # Handle text messages (replies)
        if message_type == 'text':
            result = handle_text_reply(message, message.get('from', ''))
            if result:
                return jsonify(result), 200
            else:
                return jsonify({"status": "ignored", "reason": "Untracked text message"}), 200
        
        # Handle media messages (image, video, document, audio)
        if message_type in ['image', 'video', 'document', 'audio']:
            result = handle_media_reply(message, message.get('from', ''))
            if result:
                return jsonify(result), 200
            else:
                return jsonify({"status": "ignored", "reason": "Untracked media message"}), 200
        
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
