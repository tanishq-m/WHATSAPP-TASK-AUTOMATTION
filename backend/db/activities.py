"""
Task Activities CRUD operations for the database.
Handles activity feed, comments, attachments, and submission tokens.
"""

from . import get_db_connection
from datetime import datetime, timedelta
import secrets


# ============================================================================
# SUBMISSION TOKENS
# ============================================================================

def create_submission_token(task_id, employee_id, expires_in_days=7):
    """
    Generate a unique submission token for a task.
    
    Args:
        task_id (str): Task ID
        employee_id (int): Employee ID
        expires_in_days (int): Token expiry in days (default 7)
        
    Returns:
        dict: Success response with token or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Generate secure token
            token = secrets.token_urlsafe(16)
            
            # Calculate expiry
            expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            # Insert token
            cursor.execute("""
                INSERT INTO task_submission_tokens 
                (task_id, employee_id, token, status, created_at, expires_at)
                VALUES (?, ?, ?, 'pending', CURRENT_TIMESTAMP, ?)
            """, (task_id, employee_id, token, expires_at.isoformat()))
            
            conn.commit()
            
            print(f"✅ Created submission token for task {task_id}")
            return {"success": True, "data": {"token": token}}
        
    except Exception as e:
        print(f"❌ Error creating submission token: {e}")
        return {"success": False, "error": str(e)}


def get_submission_by_token(token):
    """
    Get submission token details including task and employee info.
    
    Args:
        token (str): Submission token
        
    Returns:
        dict: Success response with submission data or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    st.*,
                    t.title as task_title,
                    t.description as task_description,
                    t.due_date as task_due_date,
                    t.priority as task_priority,
                    e.name as employee_name,
                    e.phone as employee_phone
                FROM task_submission_tokens st
                JOIN tasks t ON st.task_id = t.task_id
                JOIN employees e ON st.employee_id = e.id
                WHERE st.token = ?
            """, (token,))
            
            row = cursor.fetchone()
            
            if not row:
                return {"success": False, "error": "Token not found"}
            
            submission = dict(row)
            
            # Check if expired
            if submission.get('expires_at'):
                expires_at = datetime.fromisoformat(submission['expires_at'])
                if datetime.now() > expires_at:
                    return {"success": False, "error": "Token expired"}
            
            # Check if already submitted
            if submission.get('status') == 'submitted':
                return {"success": False, "error": "Token already used"}
            
            print(f"✅ Retrieved submission token: {token}")
            return {"success": True, "data": submission}
        
    except Exception as e:
        print(f"❌ Error getting submission: {e}")
        return {"success": False, "error": str(e)}


def mark_submission_complete(token):
    """
    Mark a submission token as completed.
    
    Args:
        token (str): Submission token
        
    Returns:
        dict: Success response or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE task_submission_tokens
                SET status = 'submitted', submitted_at = CURRENT_TIMESTAMP
                WHERE token = ?
            """, (token,))
            
            conn.commit()
            
            if cursor.rowcount == 0:
                return {"success": False, "error": "Token not found"}
            
            print(f"✅ Marked submission complete: {token}")
            return {"success": True}
        
    except Exception as e:
        print(f"❌ Error marking submission complete: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# ACTIVITIES
# ============================================================================

def create_activity(activity_data):
    """
    Create a new activity for a task.
    
    Args:
        activity_data (dict): Activity data with keys:
            - task_id (str): Task ID
            - author_type (str): 'employee', 'admin', or 'system'
            - author_id (int, optional): Author's ID
            - author_name (str): Author's display name
            - activity_type (str): 'comment', 'attachment', 'status_change', 'mention', 'system'
            - source (str): 'whatsapp_reply', 'form_submission', 'web_dashboard', 'system'
            - message (str, optional): Activity message/content
            - mentioned_user_id (int, optional): User ID if mention
            - whatsapp_message_id (str, optional): WhatsApp message ID for threading
            
    Returns:
        dict: Success response with created activity or error
    """
    try:
        from . import convert_to_iso8601
        from services import deduplication_service
        
        # Check for duplicate activity (only for non-system activities with messages)
        if activity_data.get('message') and activity_data.get('author_id'):
            is_duplicate = deduplication_service.is_activity_duplicate(
                task_id=activity_data.get('task_id'),
                author_id=activity_data.get('author_id'),
                message=activity_data.get('message'),
                author_type=activity_data.get('author_type', 'employee')
            )
            
            if is_duplicate:
                print(f"⚠️ Skipping duplicate activity creation for task {activity_data.get('task_id')}")
                return {
                    'success': False,
                    'error': 'Duplicate activity detected',
                    'duplicate': True
                }
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO task_activities (
                    task_id, author_type, author_id, author_name,
                    activity_type, source, message, mentioned_user_id,
                    whatsapp_sent, whatsapp_message_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                activity_data.get('task_id'),
                activity_data.get('author_type'),
                activity_data.get('author_id'),
                activity_data.get('author_name'),
                activity_data.get('activity_type'),
                activity_data.get('source'),
                activity_data.get('message'),
                activity_data.get('mentioned_user_id'),
                activity_data.get('whatsapp_sent', False),
                activity_data.get('whatsapp_message_id')
            ))
            
            activity_id = cursor.lastrowid
            conn.commit()
            
            # Fetch created activity
            cursor.execute("SELECT * FROM task_activities WHERE id = ?", (activity_id,))
            activity = dict(cursor.fetchone())
            
            # Convert timestamps to ISO 8601 format
            activity['created_at'] = convert_to_iso8601(activity.get('created_at'))
            activity['updated_at'] = convert_to_iso8601(activity.get('updated_at'))
            
            print(f"✅ Created activity {activity_id} for task {activity_data.get('task_id')}")
            return {"success": True, "data": activity}
        
    except Exception as e:
        print(f"❌ Error creating activity: {e}")
        return {"success": False, "error": str(e)}


def get_activities_by_task(task_id):
    """
    Get all activities for a task, ordered by newest first.
    
    Args:
        task_id (str): Task ID
        
    Returns:
        dict: Success response with list of activities or error
    """
    try:
        from . import convert_to_iso8601
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM task_activities
                WHERE task_id = ?
                ORDER BY created_at DESC, id DESC
            """, (task_id,))
            
            activities = [dict(row) for row in cursor.fetchall()]
            
            # Fetch attachments for each activity and convert timestamps
            for activity in activities:
                # Convert activity timestamp to ISO 8601 with UTC timezone
                activity['created_at'] = convert_to_iso8601(activity.get('created_at'))
                
                cursor.execute("""
                    SELECT * FROM task_activity_attachments
                    WHERE activity_id = ?
                    ORDER BY created_at
                """, (activity['id'],))
                
                attachments = [dict(row) for row in cursor.fetchall()]
                
                # Convert attachment timestamps
                for attachment in attachments:
                    attachment['created_at'] = convert_to_iso8601(attachment.get('created_at'))
                
                activity['attachments'] = attachments
            
            print(f"✅ Retrieved {len(activities)} activities for task {task_id}")
            return {"success": True, "data": activities}
        
    except Exception as e:
        print(f"❌ Error getting activities: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# ATTACHMENTS
# ============================================================================

def create_attachment(attachment_data):
    """
    Create a new attachment linked to an activity.
    
    Args:
        attachment_data (dict): Attachment data with keys:
            - activity_id (int): Activity ID
            - task_id (str): Task ID
            - media_type (str): 'image', 'video', 'document', 'audio'
            - file_path (str): Path to file on disk
            - filename (str): Original filename
            - content_type (str): MIME type
            - file_size (int): File size in bytes
            - file_hash (str, optional): SHA-256 hash of file for deduplication
            
    Returns:
        dict: Success response with created attachment or error
    """
    try:
        from . import convert_to_iso8601
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO task_activity_attachments (
                    activity_id, task_id, media_type, file_path,
                    filename, content_type, file_size, file_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                attachment_data.get('activity_id'),
                attachment_data.get('task_id'),
                attachment_data.get('media_type'),
                attachment_data.get('file_path'),
                attachment_data.get('filename'),
                attachment_data.get('content_type'),
                attachment_data.get('file_size'),
                attachment_data.get('file_hash')
            ))
            
            attachment_id = cursor.lastrowid
            conn.commit()
            
            # Fetch created attachment
            cursor.execute("SELECT * FROM task_activity_attachments WHERE id = ?", (attachment_id,))
            attachment = dict(cursor.fetchone())
            
            # Convert timestamp to ISO 8601 format
            attachment['created_at'] = convert_to_iso8601(attachment.get('created_at'))
            
            print(f"✅ Created attachment {attachment_id} for activity {attachment_data.get('activity_id')}")
            return {"success": True, "data": attachment}
        
    except Exception as e:
        print(f"❌ Error creating attachment: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# TASK MESSAGES (for WhatsApp threading)
# ============================================================================

def create_task_message(task_id, whatsapp_message_id, employee_phone, message_type='eod_check'):
    """
    Store a WhatsApp message ID for reply threading.
    
    Args:
        task_id (str): Task ID
        whatsapp_message_id (str): WhatsApp message ID from API response
        employee_phone (str): Employee phone number
        message_type (str): Type of message ('eod_check', 'mention', etc.)
        
    Returns:
        dict: Success response or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO task_messages (
                    task_id, whatsapp_message_id, employee_phone, message_type, sent_at
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (task_id, whatsapp_message_id, employee_phone, message_type))
            
            conn.commit()
            
            print(f"✅ Stored task message mapping: {task_id} -> {whatsapp_message_id}")
            return {"success": True}
        
    except Exception as e:
        print(f"❌ Error creating task message: {e}")
        return {"success": False, "error": str(e)}


def get_task_by_whatsapp_message_id(whatsapp_message_id):
    """
    Find task ID from a WhatsApp message ID (for reply threading).
    
    Args:
        whatsapp_message_id (str): WhatsApp message ID
        
    Returns:
        dict: Success response with task_id or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT task_id, employee_phone, message_type, sent_at
                FROM task_messages
                WHERE whatsapp_message_id = ?
            """, (whatsapp_message_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return {"success": False, "error": "Message mapping not found"}
            
            result = dict(row)
            print(f"✅ Found task {result['task_id']} for WhatsApp message {whatsapp_message_id}")
            return {"success": True, "data": result}
        
    except Exception as e:
        print(f"❌ Error getting task by message ID: {e}")
        return {"success": False, "error": str(e)}


def update_activity_mention_notification(activity_id, mentioned_employee_id, whatsapp_message_id):
    """
    Update activity with mention notification status.
    
    Args:
        activity_id (int): Activity ID
        mentioned_employee_id (int): Employee ID who was mentioned
        whatsapp_message_id (str): WhatsApp message ID of notification
        
    Returns:
        dict: Success response or error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE task_activities
                SET mentioned_user_id = ?,
                    mention_notification_sent = 1,
                    mention_notification_message_id = ?
                WHERE id = ?
            """, (mentioned_employee_id, whatsapp_message_id, activity_id))
            
            conn.commit()
            
            print(f"✅ Updated activity {activity_id} with mention notification")
            return {"success": True}
        
    except Exception as e:
        print(f"❌ Error updating mention notification: {e}")
        return {"success": False, "error": str(e)}
