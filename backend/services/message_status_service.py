"""
Message Status Service
Handles WhatsApp message delivery, read, and failure status tracking.
"""

from datetime import datetime
import json
import db


def update_message_status(whatsapp_message_id, status, timestamp=None, error_data=None, webhook_payload=None):
    """
    Update message status based on webhook from Kapso.
    
    Args:
        whatsapp_message_id (str): WhatsApp message ID
        status (str): 'delivered', 'read', or 'failed'
        timestamp (str): Unix timestamp from webhook
        error_data (dict): Error information if status is 'failed'
        webhook_payload (dict): Full webhook payload for history
        
    Returns:
        dict: Success response with updated message info
    """
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Find message in database
            cursor.execute("""
                SELECT id, task_id, delivered_at, read_at, failed_at 
                FROM task_messages 
                WHERE whatsapp_message_id = ?
            """, (whatsapp_message_id,))
            
            message = cursor.fetchone()
            
            if not message:
                print(f"⚠️ Message not found: {whatsapp_message_id}")
                return {
                    'success': False,
                    'error': 'Message not found',
                    'whatsapp_message_id': whatsapp_message_id
                }
            
            message_id = message['id']
            task_id = message['task_id']
            old_delivered = message['delivered_at']
            old_read = message['read_at']
            old_failed = message['failed_at']
            
            # Convert timestamp to datetime
            status_time = None
            if timestamp:
                try:
                    status_time = datetime.fromtimestamp(int(timestamp))
                except:
                    status_time = datetime.now()
            else:
                status_time = datetime.now()
            
            # Determine old status for history
            if old_read:
                old_status = 'read'
            elif old_delivered:
                old_status = 'delivered'
            elif old_failed:
                old_status = 'failed'
            else:
                old_status = 'sent'
            
            # Update message based on status type
            if status == 'delivered':
                cursor.execute("""
                    UPDATE task_messages 
                    SET delivered_at = ?
                    WHERE id = ?
                """, (status_time, message_id))
                
                print(f"✅ Message {whatsapp_message_id} marked as delivered")
                
            elif status == 'read':
                cursor.execute("""
                    UPDATE task_messages 
                    SET read_at = ?, read_receipt_available = 1, read_inferred = 0
                    WHERE id = ?
                """, (status_time, message_id))
                
                print(f"✅ Message {whatsapp_message_id} marked as read")
                
            elif status == 'failed':
                # Extract failure reason
                failure_reason = 'Unknown error'
                if error_data and isinstance(error_data, list) and len(error_data) > 0:
                    error_item = error_data[0]
                    error_code = error_item.get('code', '')
                    error_title = error_item.get('title', '')
                    error_message = error_item.get('message', '')
                    failure_reason = f"Code {error_code}: {error_title or error_message}"
                
                cursor.execute("""
                    UPDATE task_messages 
                    SET failed_at = ?, failure_reason = ?
                    WHERE id = ?
                """, (status_time, failure_reason, message_id))
                
                print(f"❌ Message {whatsapp_message_id} marked as failed: {failure_reason}")
            
            # Create status history entry
            cursor.execute("""
                INSERT INTO message_status_history 
                (message_id, whatsapp_message_id, old_status, new_status, timestamp, webhook_payload)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                message_id,
                whatsapp_message_id,
                old_status,
                status,
                status_time,
                json.dumps(webhook_payload) if webhook_payload else None
            ))
            
            conn.commit()
            
            return {
                'success': True,
                'message_id': message_id,
                'task_id': task_id,
                'status': status,
                'timestamp': status_time.isoformat(),
                'old_status': old_status
            }
            
    except Exception as e:
        print(f"❌ Error updating message status: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def infer_read_from_reply(whatsapp_message_id):
    """
    Infer that a message was read when user replies to it.
    Used when user has read receipts disabled.
    
    Args:
        whatsapp_message_id (str): WhatsApp message ID that was replied to
        
    Returns:
        dict: Success response
    """
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Find message
            cursor.execute("""
                SELECT id, task_id, read_at, read_receipt_available 
                FROM task_messages 
                WHERE whatsapp_message_id = ?
            """, (whatsapp_message_id,))
            
            message = cursor.fetchone()
            
            if not message:
                return {'success': False, 'error': 'Message not found'}
            
            # Only infer if not already marked as read
            if message['read_at']:
                print(f"ℹ️ Message {whatsapp_message_id} already marked as read")
                return {
                    'success': True,
                    'already_read': True
                }
            
            message_id = message['id']
            task_id = message['task_id']
            
            # Mark as read (inferred)
            read_time = datetime.now()
            cursor.execute("""
                UPDATE task_messages 
                SET read_at = ?, read_receipt_available = 0, read_inferred = 1
                WHERE id = ?
            """, (read_time, message_id))
            
            # Create status history entry
            cursor.execute("""
                INSERT INTO message_status_history 
                (message_id, whatsapp_message_id, old_status, new_status, timestamp, webhook_payload)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                message_id,
                whatsapp_message_id,
                'delivered',
                'read_inferred',
                read_time,
                json.dumps({'inference_reason': 'user_replied'})
            ))
            
            conn.commit()
            
            print(f"✅ Inferred read status for message {whatsapp_message_id} (user replied)")
            
            return {
                'success': True,
                'message_id': message_id,
                'task_id': task_id,
                'read_inferred': True,
                'timestamp': read_time.isoformat()
            }
            
    except Exception as e:
        print(f"❌ Error inferring read status: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def infer_read_from_task_action(task_id, employee_id):
    """
    Infer that messages were read when user performs actions on a task.
    Used when user has read receipts disabled.
    
    Args:
        task_id (str): Task ID
        employee_id (int): Employee ID who performed action
        
    Returns:
        dict: Success response with count of messages updated
    """
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get employee phone
            cursor.execute("SELECT phone FROM employees WHERE id = ?", (employee_id,))
            employee = cursor.fetchone()
            
            if not employee:
                return {'success': False, 'error': 'Employee not found'}
            
            employee_phone = employee['phone']
            
            # Find unread messages for this task and employee
            cursor.execute("""
                SELECT id, whatsapp_message_id 
                FROM task_messages 
                WHERE task_id = ? 
                  AND employee_phone = ? 
                  AND read_at IS NULL
                  AND failed_at IS NULL
            """, (task_id, employee_phone))
            
            unread_messages = cursor.fetchall()
            
            if not unread_messages:
                return {
                    'success': True,
                    'messages_updated': 0
                }
            
            read_time = datetime.now()
            updated_count = 0
            
            for message in unread_messages:
                message_id = message['id']
                whatsapp_message_id = message['whatsapp_message_id']
                
                # Mark as read (inferred)
                cursor.execute("""
                    UPDATE task_messages 
                    SET read_at = ?, read_receipt_available = 0, read_inferred = 1
                    WHERE id = ?
                """, (read_time, message_id))
                
                # Create status history entry
                cursor.execute("""
                    INSERT INTO message_status_history 
                    (message_id, whatsapp_message_id, old_status, new_status, timestamp, webhook_payload)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    message_id,
                    whatsapp_message_id,
                    'delivered',
                    'read_inferred',
                    read_time,
                    json.dumps({'inference_reason': 'task_action_performed'})
                ))
                
                updated_count += 1
            
            conn.commit()
            
            print(f"✅ Inferred read status for {updated_count} messages (user performed task action)")
            
            return {
                'success': True,
                'messages_updated': updated_count,
                'task_id': task_id,
                'timestamp': read_time.isoformat()
            }
            
    except Exception as e:
        print(f"❌ Error inferring read status from task action: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def get_message_status_history(message_id):
    """
    Get status history for a message.
    
    Args:
        message_id (int): Message ID
        
    Returns:
        dict: Success response with history entries
    """
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, whatsapp_message_id, old_status, new_status, 
                       timestamp, webhook_payload
                FROM message_status_history
                WHERE message_id = ?
                ORDER BY timestamp ASC
            """, (message_id,))
            
            history = [dict(row) for row in cursor.fetchall()]
            
            return {
                'success': True,
                'data': history
            }
            
    except Exception as e:
        print(f"❌ Error getting message status history: {e}")
        return {
            'success': False,
            'error': str(e)
        }
