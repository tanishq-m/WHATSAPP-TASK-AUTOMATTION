"""
Submissions API Blueprint
Handles form-based task submissions with file uploads
"""

from flask import Blueprint, request, jsonify
import logging
from services import submission_service

logger = logging.getLogger(__name__)

submissions_bp = Blueprint('submissions', __name__, url_prefix='/api/submissions')


@submissions_bp.route('/<token>', methods=['GET'])
def get_submission(token):
    """
    GET /api/submissions/<token>
    
    Get submission details for a given token.
    Returns task information and submission status.
    
    Response:
        200: {success: true, data: {task_id, task_title, task_description, ...}}
        400/404: {success: false, error: "..."}
    """
    try:
        result = submission_service.get_submission_details(token)
        
        if not result['success']:
            return jsonify(result), 404 if 'not found' in result.get('error', '').lower() else 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in get_submission: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@submissions_bp.route('/<token>', methods=['POST'])
def submit_task(token):
    """
    POST /api/submissions/<token>
    
    Submit task update with message and optional files.
    Creates activity entries and marks submission complete.
    
    Request Body (multipart/form-data):
        - message: Text comment (optional if files provided)
        - files: File uploads (optional, can be multiple)
    
    Response:
        200: {success: true, data: {task_id, message_posted, files_uploaded, uploaded_files}}
        400: {success: false, error: "..."}
    """
    try:
        # Get form data
        message = request.form.get('message', '').strip()
        status = request.form.get('status', '').strip()  # Optional status update
        
        # Get uploaded files
        files = request.files.getlist('files')
        
        submission_data = {
            "message": message,
            "status": status if status else None
        }
        
        result = submission_service.create_submission(token, submission_data, files if files else None)
        
        if not result['success']:
            status_code = 400
            if 'not found' in result.get('error', '').lower():
                status_code = 404
            elif 'expired' in result.get('error', '').lower() or 'already used' in result.get('error', '').lower():
                status_code = 410  # Gone
            
            return jsonify(result), status_code
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in submit_task: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@submissions_bp.route('/<token>/upload', methods=['POST'])
def upload_file(token):
    """
    POST /api/submissions/<token>/upload
    
    Upload a single file for a submission.
    Used for AJAX file uploads from the form.
    
    Request Body (multipart/form-data):
        - file: Single file upload
    
    Response:
        200: {success: true, data: {filename, file_path, content_type, file_size, media_type}}
        400: {success: false, error: "..."}
    """
    try:
        # Verify token is valid
        sub_result = submission_service.get_submission_details(token)
        if not sub_result['success']:
            return jsonify(sub_result), 404 if 'not found' in sub_result.get('error', '').lower() else 400
        
        task_id = sub_result['data']['task_id']
        
        # Get file
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        
        # Save file
        result = submission_service.save_uploaded_file(file, task_id, token)
        
        if not result['success']:
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in upload_file: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
