"""
Files API Blueprint
Handles file downloads and serving uploaded attachments
"""

from flask import Blueprint, send_file, jsonify, request, abort
from pathlib import Path
import os
import db

# Create Blueprint
files_bp = Blueprint('files', __name__)


@files_bp.route('/files/<path:file_path>')
def download_file(file_path):
    """
    Download file endpoint.
    
    GET /api/files/<file_path>
    
    Serves files from the uploads directory.
    Validates that the file exists and is accessible.
    """
    try:
        print(f"📥 File download request: {file_path}")
        
        # Security: Ensure file path doesn't contain directory traversal
        if '..' in file_path or file_path.startswith('/'):
            print(f"❌ Invalid file path: {file_path}")
            return jsonify({"error": "Invalid file path"}), 400
        
        # Construct full file path
        # file_path already includes "uploads/" from the database
        base_dir = Path(__file__).parent.parent
        full_file_path = base_dir / file_path
        
        print(f"📁 Looking for file at: {full_file_path}")
        
        # Verify file exists and is within uploads directory
        if not full_file_path.exists():
            print(f"❌ File not found: {full_file_path}")
            return jsonify({"error": "File not found"}), 404
        
        # Verify the file is within the uploads directory (security check)
        base_upload_dir = base_dir / 'uploads'
        try:
            full_file_path.resolve().relative_to(base_upload_dir.resolve())
        except ValueError:
            print(f"❌ Access denied for file: {full_file_path}")
            return jsonify({"error": "Access denied"}), 403
        
        # Optional: Verify file is linked to a valid attachment in database
        # This adds extra security by ensuring only files that were properly uploaded can be downloaded
        if verify_file_in_database(file_path):
            print(f"✅ File verified in database: {file_path}")
            return send_file(
                full_file_path,
                as_attachment=True,
                download_name=get_original_filename(file_path) or full_file_path.name
            )
        else:
            print(f"❌ File not found in database: {file_path}")
            return jsonify({"error": "File not found in system"}), 404
            
    except Exception as e:
        print(f"❌ Error serving file {file_path}: {e}")
        return jsonify({"error": "Internal server error"}), 500


def verify_file_in_database(file_path):
    """
    Verify that the file path exists in the database attachments.
    This prevents downloading files that weren't properly uploaded through the system.
    """
    try:
        with db.get_db_connection() as conn:
            result = conn.execute(
                "SELECT id FROM task_activity_attachments WHERE file_path = ?",
                (file_path,)
            ).fetchone()
            return result is not None
    except Exception as e:
        print(f"Error verifying file in database: {e}")
        return False


def get_original_filename(file_path):
    """
    Get the original filename for a file path from the database.
    This ensures the downloaded file has a user-friendly name.
    """
    try:
        with db.get_db_connection() as conn:
            result = conn.execute(
                "SELECT filename FROM task_activity_attachments WHERE file_path = ?",
                (file_path,)
            ).fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"Error getting original filename: {e}")
        return None


@files_bp.route('/files/<path:file_path>/info')
def get_file_info(file_path):
    """
    Get file information without downloading.
    
    GET /api/files/<file_path>/info
    
    Returns file metadata including size, type, original name, etc.
    """
    try:
        with db.get_db_connection() as conn:
            result = conn.execute("""
                SELECT filename, content_type, file_size, media_type, created_at
                FROM task_activity_attachments 
                WHERE file_path = ?
            """, (file_path,)).fetchone()
            
            if not result:
                return jsonify({"success": False, "error": "File not found"}), 404
            
            return jsonify({
                "success": True,
                "data": {
                    "original_filename": result[0],
                    "content_type": result[1], 
                    "file_size": result[2],
                    "media_type": result[3],
                    "uploaded_at": result[4]
                }
            })
    except Exception as e:
        print(f"Error getting file info: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500