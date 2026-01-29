"""
Submission Service - Business logic for task submissions via forms
Handles validation, file uploads, and activity creation
"""

import os
import uuid
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
import db.activities
import db.tasks

logger = logging.getLogger(__name__)

# File upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'mp4', 'mov', 'avi'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
UPLOAD_BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_media_type(content_type):
    """Determine media type from content type."""
    if content_type.startswith('image/'):
        return 'image'
    elif content_type.startswith('video/'):
        return 'video'
    elif content_type.startswith('audio/'):
        return 'audio'
    else:
        return 'document'


def get_submission_details(token):
    """
    Get submission details by token.
    Returns task and submission info if token is valid.
    """
    try:
        result = db.activities.get_submission_by_token(token)
        
        if not result['success']:
            return {
                "success": False,
                "error": result.get('error', 'Invalid or expired token')
            }
        
        submission = result['data']
        
        # Get full task details
        task_result = db.tasks.get_task_by_id(submission['task_id'])
        if not task_result['success']:
            return {
                "success": False,
                "error": "Task not found"
            }
        
        task = task_result['data']
        
        # Combine submission and task data
        response_data = {
            "token": token,
            "task_id": submission['task_id'],
            "task_title": task['title'],
            "task_description": task.get('description', ''),
            "task_priority": task.get('priority', 'medium'),
            "task_due_date": task.get('dueDate'),
            "employee_id": submission['employee_id'],
            "employee_name": submission['employee_name'],
            "status": submission['status']
        }
        
        return {"success": True, "data": response_data}
        
    except Exception as e:
        logger.error(f"Error getting submission details: {e}")
        return {"success": False, "error": str(e)}


def save_uploaded_file(file, task_id, token):
    """
    Save uploaded file to disk.
    Returns file metadata if successful.
    """
    try:
        # Validate file
        if not file or file.filename == '':
            return {"success": False, "error": "No file provided"}
        
        if not allowed_file(file.filename):
            return {
                "success": False,
                "error": f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return {
                "success": False,
                "error": f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024} MB"
            }
        
        # Create directory structure: uploads/task_id/
        task_upload_dir = os.path.join(UPLOAD_BASE_DIR, task_id)
        os.makedirs(task_upload_dir, exist_ok=True)
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}" if file_ext else uuid.uuid4().hex
        
        file_path = os.path.join(task_upload_dir, unique_filename)
        relative_path = os.path.join('uploads', task_id, unique_filename)
        
        # Save file
        file.save(file_path)
        
        file_metadata = {
            "filename": original_filename,
            "unique_filename": unique_filename,
            "file_path": relative_path,
            "content_type": file.content_type,
            "file_size": file_size,
            "media_type": get_media_type(file.content_type or '')
        }
        
        logger.info(f"✅ Saved file {original_filename} for task {task_id}")
        return {"success": True, "data": file_metadata}
        
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return {"success": False, "error": str(e)}


def create_submission(token, submission_data, files=None):
    """
    Process task submission with comment and optional files.
    Creates activity entries and marks submission as complete.
    """
    try:
        # Get submission details
        sub_result = db.activities.get_submission_by_token(token)
        if not sub_result['success']:
            return {
                "success": False,
                "error": sub_result.get('error', 'Invalid or expired token')
            }
        
        submission = sub_result['data']
        task_id = submission['task_id']
        employee_id = submission['employee_id']
        employee_name = submission['employee_name']
        
        # Extract submission text
        message = submission_data.get('message', '').strip()
        status = submission_data.get('status')  # Optional status update
        
        if not message and not files and not status:
            return {
                "success": False,
                "error": "Please provide a message, attach files, or update status"
            }
        
        # Validate status if provided
        valid_statuses = ['in_progress', 'completed', 'pending_verification']
        if status and status not in valid_statuses:
            return {
                "success": False,
                "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            }
        
        # Update task status if provided
        old_status = None
        if status:
            # Get current task to check old status
            task_result = db.tasks.get_task_by_id(task_id)
            if task_result['success']:
                old_status = task_result['data'].get('status')
            
            # Update task status
            update_result = db.tasks.update_task(task_id, {"status": status})
            if not update_result['success']:
                return {
                    "success": False,
                    "error": f"Failed to update task status: {update_result.get('error')}"
                }
            
            # Create status change activity
            status_labels = {
                'in_progress': 'In Progress',
                'completed': 'Completed',
                'pending_verification': 'Pending Verification'
            }
            
            status_activity_data = {
                "task_id": task_id,
                "author_type": "employee",
                "author_id": employee_id,
                "author_name": employee_name,
                "activity_type": "status_change",
                "source": "form_submission",
                "message": f"Changed status to {status_labels.get(status, status)}"
            }
            
            status_activity_result = db.activities.create_activity(status_activity_data)
            if not status_activity_result['success']:
                logger.warning(f"Failed to create status change activity: {status_activity_result.get('error')}")
        
        # Create comment activity
        if message:
            activity_data = {
                "task_id": task_id,
                "author_type": "employee",
                "author_id": employee_id,
                "author_name": employee_name,
                "activity_type": "comment",
                "source": "form_submission",
                "message": message
            }
            
            activity_result = db.activities.create_activity(activity_data)
            if not activity_result['success']:
                return {
                    "success": False,
                    "error": f"Failed to create activity: {activity_result.get('error')}"
                }
            
            activity_id = activity_result['data']['id']
        else:
            activity_id = None
        
        # Process file uploads
        uploaded_files = []
        if files:
            for file in files:
                # Save file
                save_result = save_uploaded_file(file, task_id, token)
                if not save_result['success']:
                    logger.warning(f"Failed to save file: {save_result.get('error')}")
                    continue
                
                file_metadata = save_result['data']
                
                # Create attachment activity
                attachment_activity_data = {
                    "task_id": task_id,
                    "author_type": "employee",
                    "author_id": employee_id,
                    "author_name": employee_name,
                    "activity_type": "attachment",
                    "source": "form_submission",
                    "message": f"Uploaded {file_metadata['filename']}"
                }
                
                attachment_activity_result = db.activities.create_activity(attachment_activity_data)
                if not attachment_activity_result['success']:
                    logger.warning(f"Failed to create attachment activity: {attachment_activity_result.get('error')}")
                    continue
                
                attachment_activity_id = attachment_activity_result['data']['id']
                
                # Create attachment record
                attachment_data = {
                    "activity_id": attachment_activity_id,
                    "task_id": task_id,
                    "media_type": file_metadata['media_type'],
                    "file_path": file_metadata['file_path'],
                    "filename": file_metadata['filename'],
                    "content_type": file_metadata['content_type'],
                    "file_size": file_metadata['file_size']
                }
                
                attachment_result = db.activities.create_attachment(attachment_data)
                if attachment_result['success']:
                    uploaded_files.append(file_metadata['filename'])
        
        # Mark submission as complete
        mark_result = db.activities.mark_submission_complete(token)
        if not mark_result['success']:
            logger.warning(f"Failed to mark submission complete: {mark_result.get('error')}")
        
        # Create system activity for submission completed
        system_activity_data = {
            "task_id": task_id,
            "author_type": "system",
            "author_id": None,
            "author_name": "System",
            "activity_type": "system",
            "source": "system",
            "message": f"{employee_name} submitted task update via form"
        }
        db.activities.create_activity(system_activity_data)
        
        logger.info(f"✅ Submission completed for task {task_id} by employee {employee_id}")
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "message_posted": bool(message),
                "files_uploaded": len(uploaded_files),
                "uploaded_files": uploaded_files,
                "status_updated": bool(status),
                "new_status": status if status else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing submission: {e}")
        return {"success": False, "error": str(e)}
