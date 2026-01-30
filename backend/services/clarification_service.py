"""
Clarification Service - Handle unlinked media clarification flow
Stage 2.4: When employee sends media not as reply to a task,
ask them which task it belongs to via interactive buttons.
"""

import os
import uuid
import requests
from datetime import datetime, timedelta, timezone
import db
import db.employees
import db.tasks
import db.activities
import services.kapso_service as kapso_service

# Configuration - defer guardrail values to production tuning
CLARIFICATION_EXPIRY_HOURS = 24
CANCEL_GRACE_PERIOD_HOURS = 1
PENDING_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'pending')
TASKS_PER_PAGE = 2  # Show 2 tasks + Other/Back button = 3 buttons max


def get_employee_active_tasks(employee_id, limit=10, offset=0):
    """
    Get employee's active tasks sorted by most recent activity.
    
    Args:
        employee_id: Employee ID
        limit: Max tasks to return
        offset: Pagination offset
        
    Returns:
        dict: {success, data: [{task_id, title, last_activity_at}, ...], total_count}
    """
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get tasks with most recent activity first
            # Join with task_activities to get last_activity_at
            cursor.execute("""
                SELECT 
                    t.task_id,
                    t.title,
                    t.status,
                    t.priority,
                    t.updated_at,
                    COALESCE(
                        (SELECT MAX(created_at) FROM task_activities WHERE task_id = t.task_id),
                        t.updated_at
                    ) as last_activity_at
                FROM tasks t
                WHERE t.employee_id = ?
                  AND t.status NOT IN ('completed', 'cancelled')
                ORDER BY last_activity_at DESC
                LIMIT ? OFFSET ?
            """, (employee_id, limit, offset))
            
            tasks = [dict(row) for row in cursor.fetchall()]
            
            # Get total count for pagination
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM tasks
                WHERE employee_id = ?
                  AND status NOT IN ('completed', 'cancelled')
            """, (employee_id,))
            
            total = cursor.fetchone()['count']
            
            return {
                'success': True,
                'data': tasks,
                'total_count': total
            }
            
    except Exception as e:
        print(f"❌ Error getting employee active tasks: {e}")
        return {'success': False, 'error': str(e)}


def download_media_to_pending(media_url, employee_id, filename, content_type):
    """
    Download media file to pending folder for later linking.
    
    Args:
        media_url: URL to download from
        employee_id: Employee ID for folder organization
        filename: Original filename
        content_type: MIME type
        
    Returns:
        dict: {success, file_path, file_size} or {success: False, error}
    """
    try:
        # Create pending directory for this employee
        employee_dir = os.path.join(PENDING_UPLOAD_DIR, str(employee_id))
        os.makedirs(employee_dir, exist_ok=True)
        
        # Generate unique filename
        file_ext = filename.split('.')[-1] if '.' in filename else ''
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}" if file_ext else uuid.uuid4().hex
        file_path = os.path.join(employee_dir, unique_filename)
        
        # Download file
        response = requests.get(media_url, timeout=30)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        file_size = len(response.content)
        print(f"✅ Downloaded pending media: {file_path} ({file_size} bytes)")
        
        return {
            'success': True,
            'file_path': file_path,
            'file_size': file_size
        }
        
    except Exception as e:
        print(f"❌ Error downloading pending media: {e}")
        return {'success': False, 'error': str(e)}


def create_pending_clarification(employee_id, phone, media_url, media_type, caption, temp_file_path):
    """
    Create a pending clarification record and send task selection buttons.
    
    Args:
        employee_id: Employee ID
        phone: Phone number
        media_url: Original media URL
        media_type: Type of media (image, video, document, audio)
        caption: Media caption if any
        temp_file_path: Path to downloaded temp file
        
    Returns:
        dict: {success, clarification_id, message_sent} or {success: False, error}
    """
    try:
        # Get employee's active tasks
        tasks_result = get_employee_active_tasks(employee_id, limit=TASKS_PER_PAGE, offset=0)
        
        if not tasks_result['success']:
            return {'success': False, 'error': 'Failed to get employee tasks'}
        
        tasks = tasks_result['data']
        total_tasks = tasks_result['total_count']
        
        # Calculate expiry
        expires_at = datetime.now(timezone.utc) + timedelta(hours=CLARIFICATION_EXPIRY_HOURS)
        
        # Insert pending clarification record
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO pending_clarifications 
                (employee_id, phone, media_url, media_type, caption, temp_file_path,
                 status, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', datetime('now'), ?)
            """, (
                employee_id,
                phone,
                media_url,
                media_type,
                caption,
                temp_file_path,
                expires_at.isoformat()
            ))
            
            clarification_id = cursor.lastrowid
            conn.commit()
        
        # Handle case: no active tasks
        if total_tasks == 0:
            clean_phone = phone.replace('+', '')
            kapso_service.send_text_message(
                clean_phone,
                "📎 I received your media, but you don't have any active tasks to attach it to.\n\n"
                "The media will be kept for 24 hours. Once a task is assigned to you, "
                "you can send the media again as a reply to that task."
            )
            return {
                'success': True,
                'clarification_id': clarification_id,
                'message_sent': True,
                'no_tasks': True
            }
        
        # Build task list for body text
        task_list = []
        for idx, task in enumerate(tasks, 1):
            task_list.append(f"Task {idx} - {task['title']}")
        
        # Build task selection buttons
        buttons = []
        for idx, task in enumerate(tasks, 1):
            buttons.append({
                'id': f"clarify_task_{task['task_id']}_{clarification_id}",
                'title': f"Task {idx}"
            })
        
        # Add navigation button if more tasks exist
        if total_tasks > TASKS_PER_PAGE:
            buttons.append({
                'id': f"clarify_page_1_{clarification_id}",  # Page 1 = offset TASKS_PER_PAGE
                'title': "📋 Other Tasks"
            })
        else:
            # Add cancel button
            buttons.append({
                'id': f"clarify_cancel_{clarification_id}",
                'title': "❌ Cancel"
            })
        
        # Send interactive buttons
        clean_phone = phone.replace('+', '')
        body_text = (
            f"📎 I received your {media_type}"
            + (f' "{caption}"' if caption else "")
            + ".\n\nWhich task is this for?\n\n"
            + "\n".join(task_list)
        )
        
        result = kapso_service.send_interactive_buttons(
            phone_number=clean_phone,
            body_text=body_text,
            buttons=buttons,
            footer_text="Reply within 24 hours"
        )
        
        # Store the clarification message ID for tracking
        if result.get('success') and result.get('message_id'):
            with db.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE pending_clarifications
                    SET clarification_message_id = ?
                    WHERE id = ?
                """, (result['message_id'], clarification_id))
                conn.commit()
        
        return {
            'success': True,
            'clarification_id': clarification_id,
            'message_sent': result.get('success', False),
            'tasks_shown': len(tasks),
            'total_tasks': total_tasks
        }
        
    except Exception as e:
        print(f"❌ Error creating pending clarification: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def send_clarification_page(clarification_id, page_number, phone):
    """
    Send a page of task buttons for clarification.
    
    Args:
        clarification_id: Clarification record ID
        page_number: Page number (0-indexed for offset calculation)
        phone: Phone number
        
    Returns:
        dict: {success, message_sent}
    """
    try:
        # Get clarification record
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM pending_clarifications WHERE id = ?
            """, (clarification_id,))
            clarification = cursor.fetchone()
            
            if not clarification:
                return {'success': False, 'error': 'Clarification not found'}
            
            clarification = dict(clarification)
        
        employee_id = clarification['employee_id']
        offset = page_number * TASKS_PER_PAGE
        
        # Get tasks for this page
        tasks_result = get_employee_active_tasks(employee_id, limit=TASKS_PER_PAGE, offset=offset)
        
        if not tasks_result['success']:
            return {'success': False, 'error': 'Failed to get tasks'}
        
        tasks = tasks_result['data']
        total_tasks = tasks_result['total_count']
        
        # Build task list for body text
        task_list = []
        start_index = offset + 1
        for idx, task in enumerate(tasks, start_index):
            task_list.append(f"Task {idx} - {task['title']}")
        
        # Build buttons
        buttons = []
        
        for idx, task in enumerate(tasks, start_index):
            buttons.append({
                'id': f"clarify_task_{task['task_id']}_{clarification_id}",
                'title': f"Task {idx}"
            })
        
        # Calculate if there are more pages
        has_more = (offset + len(tasks)) < total_tasks
        has_prev = page_number > 0
        
        # Add navigation buttons (max 3 total, so plan carefully)
        if len(buttons) < 3:
            if has_prev:
                buttons.append({
                    'id': f"clarify_page_{page_number - 1}_{clarification_id}",
                    'title': "⬅️ Back"
                })
            if has_more and len(buttons) < 3:
                buttons.append({
                    'id': f"clarify_page_{page_number + 1}_{clarification_id}",
                    'title': "➡️ More"
                })
            if len(buttons) < 3:
                buttons.append({
                    'id': f"clarify_cancel_{clarification_id}",
                    'title': "❌ Cancel"
                })
        else:
            # All 3 slots used by tasks, need to make room for navigation
            # Replace last task with "More" if there are more tasks
            if has_more:
                buttons[-1] = {
                    'id': f"clarify_page_{page_number + 1}_{clarification_id}",
                    'title': "➡️ More"
                }
            elif has_prev:
                buttons[-1] = {
                    'id': f"clarify_page_{page_number - 1}_{clarification_id}",
                    'title': "⬅️ Back"
                }
        
        # Ensure we have at least a back button if on page > 0
        if has_prev and not any('Back' in btn.get('title', '') for btn in buttons):
            if len(buttons) >= 3:
                buttons[2] = {
                    'id': f"clarify_page_{page_number - 1}_{clarification_id}",
                    'title': "⬅️ Back"
                }
            else:
                buttons.append({
                    'id': f"clarify_page_{page_number - 1}_{clarification_id}",
                    'title': "⬅️ Back"
                })
        
        # Send buttons
        clean_phone = phone.replace('+', '')
        page_info = f" (Page {page_number + 1})" if page_number > 0 else ""
        
        body_text = f"📋 Select a task{page_info}:\n\n" + "\n".join(task_list)
        
        result = kapso_service.send_interactive_buttons(
            phone_number=clean_phone,
            body_text=body_text,
            buttons=buttons,
            footer_text="Reply within 24 hours"
        )
        
        return {
            'success': True,
            'action': 'page',
            'message_sent': result.get('success', False),
            'page': page_number,
            'tasks_shown': len(tasks)
        }
        
    except Exception as e:
        print(f"❌ Error sending clarification page: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def resolve_clarification(clarification_id, task_id):
    """
    Resolve a pending clarification by linking media to a task.
    
    Args:
        clarification_id: Clarification record ID
        task_id: Task to link the media to
        
    Returns:
        dict: {success, activity_created, attachment_created}
    """
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get clarification record
            cursor.execute("""
                SELECT * FROM pending_clarifications WHERE id = ?
            """, (clarification_id,))
            clarification = cursor.fetchone()
            
            if not clarification:
                return {'success': False, 'error': 'Clarification not found'}
            
            clarification = dict(clarification)
            
            if clarification['status'] != 'pending':
                return {'success': False, 'error': f"Clarification already {clarification['status']}"}
        
        employee_id = clarification['employee_id']
        temp_file_path = clarification['temp_file_path']
        media_type = clarification['media_type']
        caption = clarification['caption'] or ''
        
        # Get employee info
        employee_result = db.employees.get_employee_by_id(employee_id)
        if not employee_result['success']:
            return {'success': False, 'error': 'Employee not found'}
        
        employee = employee_result['data']
        
        # Get task info
        task_result = db.tasks.get_task_by_id(task_id)
        if not task_result['success']:
            return {'success': False, 'error': 'Task not found'}
        
        task = task_result['data']
        
        # Move file from pending to task folder
        task_upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', task_id)
        os.makedirs(task_upload_dir, exist_ok=True)
        
        # Generate new filename in task folder
        filename = os.path.basename(temp_file_path)
        new_file_path = os.path.join(task_upload_dir, filename)
        
        # Move the file
        import shutil
        shutil.move(temp_file_path, new_file_path)
        
        # Get file size
        file_size = os.path.getsize(new_file_path)
        
        # Create activity record
        activity_data = {
            'task_id': task_id,
            'author_type': 'employee',
            'author_id': employee_id,
            'author_name': employee['name'],
            'activity_type': 'attachment',
            'source': 'whatsapp_clarification',
            'message': f"Shared {media_type}" + (f": {caption}" if caption else "")
        }
        
        activity_result = db.activities.create_activity(activity_data)
        
        if not activity_result['success']:
            return {'success': False, 'error': 'Failed to create activity'}
        
        activity_id = activity_result['data']['id']
        
        # Create attachment record
        media_type_map = {
            'image': 'image',
            'video': 'video',
            'document': 'document',
            'audio': 'audio'
        }
        
        # Guess content type from extension
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        content_type_map = {
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif',
            'mp4': 'video/mp4', 'mov': 'video/quicktime',
            'pdf': 'application/pdf', 'doc': 'application/msword',
            'mp3': 'audio/mpeg', 'wav': 'audio/wav'
        }
        content_type = content_type_map.get(ext, f'{media_type}/unknown')
        
        attachment_data = {
            'activity_id': activity_id,
            'task_id': task_id,
            'media_type': media_type_map.get(media_type, 'document'),
            'file_path': new_file_path,
            'filename': filename,
            'content_type': content_type,
            'file_size': file_size
        }
        
        attachment_result = db.activities.create_attachment(attachment_data)
        
        # Update clarification status
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE pending_clarifications
                SET status = 'resolved',
                    resolved_task_id = ?,
                    resolved_at = datetime('now')
                WHERE id = ?
            """, (task_id, clarification_id))
            conn.commit()
        
        # Send confirmation to employee
        clean_phone = clarification['phone'].replace('+', '')
        kapso_service.send_text_message(
            clean_phone,
            f"✅ Your {media_type} has been attached to task:\n📋 {task['title']}"
        )
        
        return {
            'success': True,
            'action': 'resolved',
            'activity_created': True,
            'attachment_created': attachment_result.get('success', False),
            'task_id': task_id,
            'task_title': task['title']
        }
        
    except Exception as e:
        print(f"❌ Error resolving clarification: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def cancel_clarification(clarification_id, phone):
    """
    Cancel a pending clarification. Keep file for 1 hour grace period.
    
    Args:
        clarification_id: Clarification record ID
        phone: Phone number to send confirmation
        
    Returns:
        dict: {success}
    """
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Update status to cancelled with timestamp
            cursor.execute("""
                UPDATE pending_clarifications
                SET status = 'cancelled',
                    cancelled_at = datetime('now')
                WHERE id = ? AND status = 'pending'
            """, (clarification_id,))
            
            if cursor.rowcount == 0:
                return {'success': False, 'error': 'Clarification not found or already processed'}
            
            conn.commit()
        
        # Send confirmation
        clean_phone = phone.replace('+', '')
        kapso_service.send_text_message(
            clean_phone,
            "❌ Media upload cancelled.\n\n"
            "The file will be kept for 1 hour in case you change your mind. "
            "Just send it again to attach it to a task."
        )
        
        return {'success': True, 'action': 'cancelled'}
        
    except Exception as e:
        print(f"❌ Error cancelling clarification: {e}")
        return {'success': False, 'error': str(e)}


def cleanup_expired_clarifications():
    """
    Clean up expired and cancelled clarifications.
    - Delete pending clarifications older than CLARIFICATION_EXPIRY_HOURS
    - Delete cancelled clarifications older than CANCEL_GRACE_PERIOD_HOURS
    
    Returns:
        dict: {success, deleted_count, files_deleted}
    """
    try:
        files_deleted = 0
        deleted_count = 0
        
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get expired pending clarifications (24 hours)
            cursor.execute("""
                SELECT id, temp_file_path FROM pending_clarifications
                WHERE status = 'pending'
                  AND expires_at < datetime('now')
            """)
            expired_pending = cursor.fetchall()
            
            # Get cancelled clarifications past grace period (1 hour)
            cursor.execute("""
                SELECT id, temp_file_path FROM pending_clarifications
                WHERE status = 'cancelled'
                  AND cancelled_at < datetime('now', '-1 hour')
            """)
            expired_cancelled = cursor.fetchall()
            
            all_expired = [dict(row) for row in expired_pending] + [dict(row) for row in expired_cancelled]
            
            for record in all_expired:
                # Delete file if it exists
                file_path = record.get('temp_file_path')
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        files_deleted += 1
                        print(f"🗑️ Deleted expired file: {file_path}")
                    except Exception as e:
                        print(f"⚠️ Could not delete file {file_path}: {e}")
                
                # Delete record
                cursor.execute("DELETE FROM pending_clarifications WHERE id = ?", (record['id'],))
                deleted_count += 1
            
            conn.commit()
        
        print(f"✅ Cleanup complete: {deleted_count} records, {files_deleted} files deleted")
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'files_deleted': files_deleted
        }
        
    except Exception as e:
        print(f"❌ Error cleaning up clarifications: {e}")
        return {'success': False, 'error': str(e)}


def handle_clarification_button(button_id, phone):
    """
    Handle a clarification button click.
    
    Button ID formats:
    - clarify_task_{task_id}_{clarification_id} - Link to task
    - clarify_page_{page_num}_{clarification_id} - Show page of tasks
    - clarify_cancel_{clarification_id} - Cancel clarification
    
    Args:
        button_id: Button ID string
        phone: Phone number
        
    Returns:
        dict: {success, action, ...}
    """
    try:
        parts = button_id.split('_')
        
        if len(parts) < 3:
            return {'success': False, 'error': 'Invalid button ID format'}
        
        action = parts[1]  # task, page, or cancel
        
        if action == 'task':
            # clarify_task_{task_id}_{clarification_id}
            # Task ID could be like "task_001" so rejoin properly
            clarification_id = int(parts[-1])
            task_id = '_'.join(parts[2:-1])  # Everything between 'task' and clarification_id
            
            return resolve_clarification(clarification_id, task_id)
            
        elif action == 'page':
            # clarify_page_{page_num}_{clarification_id}
            page_num = int(parts[2])
            clarification_id = int(parts[3])
            
            return send_clarification_page(clarification_id, page_num, phone)
            
        elif action == 'cancel':
            # clarify_cancel_{clarification_id}
            clarification_id = int(parts[2])
            
            return cancel_clarification(clarification_id, phone)
            
        else:
            return {'success': False, 'error': f'Unknown action: {action}'}
            
    except Exception as e:
        print(f"❌ Error handling clarification button: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
