"""
Webhooks API Blueprint
Handles incoming webhook requests from external services (e.g., Kapso for WhatsApp).
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import db
import db.tasks
import db.employees
import db.activities
import services.kapso_service as kapso_service
import services.deduplication_service as dedup_service
import services.clarification_service as clarification_service
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
        context = message_data.get('context')
        replied_to_msg_id = context.get('id') if context else None
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
                
                # Initialize file tracking variables
                file_hash = None
                file_is_duplicate = False
                
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
                    
                    # Compute file hash for deduplication (Stage 2.5)
                    file_hash = dedup_service.compute_file_hash(file_path)
                    
                    # Check for duplicate file
                    if dedup_service.is_file_duplicate(file_hash, task_id):
                        print(f"⚠️ Duplicate file detected (hash: {file_hash[:16]}...)")
                        # Keep the file but mark it as duplicate in response
                        file_is_duplicate = True
                    else:
                        file_is_duplicate = False
                    
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
                        'file_size': file_size,
                        'file_hash': file_hash  # Add file hash for deduplication
                    }
                    
                    attachment_result = db.activities.create_attachment(attachment_data)
                    
                    if attachment_result['success']:
                        print(f"✅ Created attachment record for {filename}")
                        
                        if file_is_duplicate:
                            print(f"ℹ️ File is a duplicate but was saved")
                        
                        # Infer read status from media reply (Stage 2.2 - Phase 2)
                        import services.message_status_service as message_status_service
                        infer_result = message_status_service.infer_read_from_reply(replied_to_msg_id)
                        if infer_result['success']:
                            print(f"✅ Inferred read status from media reply")
                        
                        return {
                            'status': 'processed',
                            'task_id': task_id,
                            'media_saved': True,
                            'filename': filename,
                            'is_duplicate': file_is_duplicate
                        }
                    else:
                        print(f"❌ Failed to create attachment record: {attachment_result.get('error')}")
                else:
                    print(f"❌ Failed to create activity: {activity_result.get('error')}")
            else:
                print(f"ℹ️ Media message not linked to tracked task - initiating clarification")
                
                # Get employee by phone
                employee_result = db.employees.get_employee_by_phone(phone_number)
                if not employee_result['success']:
                    print(f"⚠️ Unknown phone number {phone_number}, ignoring media")
                    return None
                
                employee = employee_result['data']
                
                # Download media to pending folder
                download_result = clarification_service.download_media_to_pending(
                    media_url=media_url,
                    employee_id=employee['id'],
                    filename=filename,
                    content_type=content_type
                )
                
                if not download_result['success']:
                    print(f"❌ Failed to download pending media: {download_result.get('error')}")
                    return None
                
                # Create pending clarification and send buttons
                clarification_result = clarification_service.create_pending_clarification(
                    employee_id=employee['id'],
                    phone=phone_number,
                    media_url=media_url,
                    media_type=message_type,
                    caption=caption,
                    temp_file_path=download_result['file_path']
                )
                
                if clarification_result['success']:
                    print(f"✅ Created clarification {clarification_result.get('clarification_id')}")
                    return {
                        'status': 'clarification_requested',
                        'clarification_id': clarification_result.get('clarification_id'),
                        'tasks_shown': clarification_result.get('tasks_shown', 0)
                    }
                else:
                    print(f"❌ Failed to create clarification: {clarification_result.get('error')}")
                    return None
        else:
            print(f"ℹ️ Media message without reply context - initiating clarification")
            
            # Same clarification logic for media without context
            employee_result = db.employees.get_employee_by_phone(phone_number)
            if not employee_result['success']:
                print(f"⚠️ Unknown phone number {phone_number}, ignoring media")
                return None
            
            employee = employee_result['data']
            
            # Get Kapso media info
            kapso_data = message_data.get('kapso', {})
            media_url = kapso_data.get('media_url')
            media_data = kapso_data.get('media_data', {})
            message_type = message_data.get('type', 'document')
            media_info = message_data.get(message_type, {})
            filename = media_data.get('filename', f'media_{message_data.get("id", "unknown")}')
            content_type = media_data.get('content_type', f'{message_type}/unknown')
            caption = media_info.get('caption', '')
            
            if not media_url:
                print("❌ No media URL for clarification")
                return None
            
            # Download and create clarification
            download_result = clarification_service.download_media_to_pending(
                media_url=media_url,
                employee_id=employee['id'],
                filename=filename,
                content_type=content_type
            )
            
            if not download_result['success']:
                return None
            
            clarification_result = clarification_service.create_pending_clarification(
                employee_id=employee['id'],
                phone=phone_number,
                media_url=media_url,
                media_type=message_type,
                caption=caption,
                temp_file_path=download_result['file_path']
            )
            
            if clarification_result['success']:
                return {
                    'status': 'clarification_requested',
                    'clarification_id': clarification_result.get('clarification_id')
                }
            
            return None
        
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
        context = message_data.get('context')
        replied_to_msg_id = context.get('id') if context else None
        
        # Get message text
        text_data = message_data.get('text', {})
        message_body = text_data.get('body', '').strip()
        
        if not message_body:
            print("ℹ️ Empty message body, ignoring")
            return None
        
        print(f"💬 Text message: {message_body}")
        print(f"🔗 Reply to message ID: {replied_to_msg_id}")
        
        # If not a reply, check if it's a help request first
        if not replied_to_msg_id:
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
            
            # Otherwise send guidance message
            print("ℹ️ Text message not a reply to any task - sending guidance")
            clean_phone = phone_number.replace('+', '')
            kapso_service.send_text_message(
                clean_phone,
                "💬 To add a comment to a task, please reply directly to any task message.\n\n"
                "Or you can select a task from the list of your active tasks by sending any media (image/document)."
            )
            return None
        
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
                    
                    # Infer read status from reply (Stage 2.2 - Phase 2)
                    import services.message_status_service as message_status_service
                    infer_result = message_status_service.infer_read_from_reply(replied_to_msg_id)
                    if infer_result['success']:
                        print(f"✅ Inferred read status from reply")
                    
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
        
        # Untracked text message
        print(f"ℹ️ Untracked text message, ignoring")
        return None
        
    except Exception as e:
        print(f"❌ Error handling text reply: {e}")
        import traceback
        traceback.print_exc()
        return None


def handle_status_webhook(payload):
    """
    Handle status webhooks from Kapso (delivery, read, failed).
    
    Webhook format:
    {
        "statuses": [
            {
                "id": "wamid.xxx",
                "status": "delivered|read|failed",
                "timestamp": "1234567890",
                "recipient_id": "918005800336",
                "errors": [...]  # Only for failed status
            }
        ]
    }
    """
    try:
        import services.message_status_service as message_status_service
        
        statuses = payload.get('statuses', [])
        
        print(f"\n📊 STATUS WEBHOOK RECEIVED")
        print(f"📦 Statuses count: {len(statuses)}")
        
        results = []
        
        for status_item in statuses:
            whatsapp_message_id = status_item.get('id')
            status = status_item.get('status')
            timestamp = status_item.get('timestamp')
            recipient_id = status_item.get('recipient_id')
            errors = status_item.get('errors')
            
            print(f"\n📨 Message ID: {whatsapp_message_id}")
            print(f"📊 Status: {status}")
            print(f"📅 Timestamp: {timestamp}")
            print(f"👤 Recipient: {recipient_id}")
            
            if not whatsapp_message_id or not status:
                print(f"⚠️ Invalid status item, missing required fields")
                results.append({
                    'status': 'error',
                    'error': 'Missing required fields'
                })
                continue
            
            # Check for duplicate status updates
            with db.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check webhook deduplication table using webhook_id
                # Format: status_{whatsapp_message_id}_{status}
                webhook_id = f"status_{whatsapp_message_id}_{status}"
                
                cursor.execute("""
                    SELECT id FROM webhook_deduplication 
                    WHERE webhook_id = ?
                """, (webhook_id,))
                
                existing = cursor.fetchone()
                
                if existing:
                    print(f"⚠️ Duplicate status webhook, ignoring")
                    results.append({
                        'status': 'ignored',
                        'reason': 'Duplicate status update',
                        'whatsapp_message_id': whatsapp_message_id
                    })
                    continue
                
                # Record this webhook
                cursor.execute("""
                    INSERT INTO webhook_deduplication 
                    (webhook_id, webhook_type, phone, processed_at, payload_hash)
                    VALUES (?, ?, ?, datetime('now'), ?)
                """, (
                    webhook_id,
                    'status_update',
                    recipient_id,
                    str(hash(str(payload)))[:50]  # Simple hash for dedup
                ))
                
                conn.commit()
            
            # Update message status
            result = message_status_service.update_message_status(
                whatsapp_message_id=whatsapp_message_id,
                status=status,
                timestamp=timestamp,
                error_data=errors,
                webhook_payload=payload
            )
            
            results.append(result)
        
        # Summary
        success_count = sum(1 for r in results if r.get('success'))
        print(f"\n✅ Processed {success_count}/{len(statuses)} status updates")
        
        return {
            'status': 'processed',
            'total': len(statuses),
            'success': success_count,
            'results': results
        }
        
    except Exception as e:
        print(f"❌ Error handling status webhook: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'error': str(e)
        }


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
        
        # ============================================================================
        # DEDUPLICATION CHECK - Stage 2.5
        # Prevent duplicate webhook processing using payload hash
        # ============================================================================
        
        # Extract unique webhook identifier
        message = payload.get('message', {})
        message_id = message.get('id')  # WhatsApp message ID
        phone_number = message.get('from', '')
        
        # For status webhooks, use first status item
        if 'statuses' in payload and payload['statuses']:
            status_item = payload['statuses'][0]
            message_id = status_item.get('id')
            phone_number = status_item.get('recipient_id', '')
        
        # Check if webhook already processed
        if message_id:
            if dedup_service.is_webhook_processed(message_id, phone_number):
                print(f"⚠️ Duplicate webhook detected, ignoring (message_id: {message_id})")
                return jsonify({
                    "status": "ignored", 
                    "reason": "Duplicate webhook",
                    "message_id": message_id
                }), 200
            
            # Check using payload hash as well
            payload_hash = dedup_service.compute_payload_hash(payload)
            with db.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM webhook_deduplication 
                    WHERE payload_hash = ? AND processed_at > datetime('now', '-1 hour')
                """, (payload_hash,))
                if cursor.fetchone():
                    print(f"⚠️ Duplicate webhook detected by payload hash, ignoring")
                    return jsonify({
                        "status": "ignored",
                        "reason": "Duplicate webhook (payload hash match)"
                    }), 200
        
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
                # Mark webhook as processed
                if message_id:
                    dedup_service.mark_webhook_processed(
                        webhook_id=message_id,
                        webhook_type='text_reply',
                        phone=phone_number,
                        payload=payload
                    )
                return jsonify(result), 200
            else:
                return jsonify({"status": "ignored", "reason": "Untracked text message"}), 200
        
        # Handle media messages (image, video, document, audio)
        if message_type in ['image', 'video', 'document', 'audio']:
            result = handle_media_reply(message, message.get('from', ''))
            if result:
                # Mark webhook as processed
                if message_id:
                    dedup_service.mark_webhook_processed(
                        webhook_id=message_id,
                        webhook_type=f'media_{message_type}',
                        phone=phone_number,
                        payload=payload
                    )
                return jsonify(result), 200
            else:
                return jsonify({"status": "ignored", "reason": "Untracked media message"}), 200
        
        # Handle status webhooks (delivery, read, failed)
        # Kapso sends status updates in a 'statuses' array
        if 'statuses' in payload:
            result = handle_status_webhook(payload)
            # Status webhook handler already marks as processed internally
            return jsonify(result), 200
        
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
        # Handle clarification buttons (Stage 2.4)
        elif reply_option_id.startswith('clarify_'):
            print(f"📎 Processing clarification button: {reply_option_id}")
            
            result = clarification_service.handle_clarification_button(reply_option_id, phone_number)
            
            if result['success']:
                # Mark webhook as processed
                if message_id:
                    dedup_service.mark_webhook_processed(
                        webhook_id=message_id,
                        webhook_type='clarification_button',
                        phone=phone_number,
                        payload=payload
                    )
                
                return jsonify({
                    'status': 'processed',
                    'action': result.get('action', 'clarification_handled'),
                    **result
                }), 200
            else:
                return jsonify({
                    'status': 'error',
                    'error': result.get('error', 'Failed to handle clarification')
                }), 200
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
            
            # Mark webhook as processed (Stage 2.5 - Deduplication)
            if message_id:
                dedup_service.mark_webhook_processed(
                    webhook_id=message_id,
                    webhook_type='button_reply',
                    phone=phone_number,
                    payload=payload
                )
                print(f"✅ Webhook marked as processed (message_id: {message_id})")
            
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
