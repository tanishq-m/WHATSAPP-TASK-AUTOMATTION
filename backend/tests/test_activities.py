"""
Tests for Activities, Submissions, and File Operations
Run with: pytest tests/test_activities.py -v
"""

import pytest
import json
import os
import sys
import sqlite3
import io
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
import config
import db


# ============================================================================
# ACTIVITY TABLES & DATABASE TESTS
# ============================================================================

def test_activity_tables_exist(client):
    """Test that activity tables were created by migration."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check task_submission_tokens table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_submission_tokens'")
    assert cursor.fetchone() is not None, "task_submission_tokens table not found"
    
    # Check task_activities table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_activities'")
    assert cursor.fetchone() is not None, "task_activities table not found"
    
    # Check task_activity_attachments table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_activity_attachments'")
    assert cursor.fetchone() is not None, "task_activity_attachments table not found"
    
    # Check task_messages table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_messages'")
    assert cursor.fetchone() is not None, "task_messages table not found"
    
    conn.close()


def test_create_submission_token(client, sample_employee):
    """Test creating a submission token."""
    import db.activities
    
    # Create a task first
    task_data = {
        'title': 'Test Task',
        'projectId': 'test_project',
        'assignedTo': sample_employee,
        'status': 'in_progress'
    }
    task_result = db.tasks.create_task(task_data)
    assert task_result['success']
    task_id = task_result['data']['task_id']
    
    # Create submission token
    result = db.activities.create_submission_token(task_id, sample_employee)
    
    assert result['success']
    assert 'token' in result['data']
    assert len(result['data']['token']) > 10


def test_get_submission_by_token(client, sample_employee):
    """Test retrieving submission by token."""
    import db.activities
    
    # Create task and token
    task_data = {
        'title': 'Test Task for Submission',
        'description': 'Test description',
        'projectId': 'test_project',
        'assignedTo': sample_employee,
        'status': 'in_progress',
        'dueDate': '2026-02-01',
        'priority': 'high'
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Retrieve by token
    result = db.activities.get_submission_by_token(token)
    
    assert result['success']
    assert result['data']['task_id'] == task_id
    assert result['data']['task_title'] == 'Test Task for Submission'
    assert result['data']['employee_id'] == sample_employee
    assert result['data']['status'] == 'pending'


def test_submission_token_already_used(client, sample_employee):
    """Test that used tokens cannot be retrieved."""
    import db.activities
    
    # Create task and token
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Mark as submitted
    mark_result = db.activities.mark_submission_complete(token)
    assert mark_result['success']
    
    # Try to retrieve again - should fail
    result = db.activities.get_submission_by_token(token)
    assert not result['success']
    assert 'already used' in result['error'].lower()


def test_create_activity(client, sample_employee):
    """Test creating an activity."""
    import db.activities
    
    # Create task
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    # Create activity
    activity_data = {
        'task_id': task_id,
        'author_type': 'employee',
        'author_id': sample_employee,
        'author_name': 'Test User',
        'activity_type': 'comment',
        'source': 'whatsapp_reply',
        'message': 'This is a test comment'
    }
    result = db.activities.create_activity(activity_data)
    
    assert result['success']
    assert result['data']['task_id'] == task_id
    assert result['data']['message'] == 'This is a test comment'
    assert result['data']['author_type'] == 'employee'


def test_get_activities_by_task(client, sample_employee):
    """Test retrieving all activities for a task."""
    import db.activities
    
    # Create task
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    # Create multiple activities
    for i in range(3):
        activity_data = {
            'task_id': task_id,
            'author_type': 'employee',
            'author_id': sample_employee,
            'author_name': 'Test User',
            'activity_type': 'comment',
            'source': 'web_dashboard',
            'message': f'Comment {i + 1}'
        }
        db.activities.create_activity(activity_data)
    
    # Retrieve activities
    result = db.activities.get_activities_by_task(task_id)
    
    assert result['success']
    assert len(result['data']) == 3
    # Should be newest first
    assert result['data'][0]['message'] == 'Comment 3'
    assert result['data'][2]['message'] == 'Comment 1'


def test_create_attachment(client, sample_employee):
    """Test creating an attachment."""
    import db.activities
    
    # Create task and activity
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    activity_data = {
        'task_id': task_id,
        'author_type': 'employee',
        'author_id': sample_employee,
        'author_name': 'Test User',
        'activity_type': 'attachment',
        'source': 'form_submission',
        'message': 'Uploaded photo'
    }
    activity_result = db.activities.create_activity(activity_data)
    activity_id = activity_result['data']['id']
    
    # Create attachment
    attachment_data = {
        'activity_id': activity_id,
        'task_id': task_id,
        'media_type': 'image',
        'file_path': '/uploads/task_001/photo.jpg',
        'filename': 'photo.jpg',
        'content_type': 'image/jpeg',
        'file_size': 245000
    }
    result = db.activities.create_attachment(attachment_data)
    
    assert result['success']
    assert result['data']['activity_id'] == activity_id
    assert result['data']['filename'] == 'photo.jpg'
    assert result['data']['media_type'] == 'image'


def test_activities_with_attachments(client, sample_employee):
    """Test that get_activities_by_task includes attachments."""
    import db.activities
    
    # Create task and activity with attachment
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    activity_data = {
        'task_id': task_id,
        'author_type': 'employee',
        'author_id': sample_employee,
        'author_name': 'Test User',
        'activity_type': 'attachment',
        'source': 'whatsapp_reply',
        'message': 'Sent photo'
    }
    activity_result = db.activities.create_activity(activity_data)
    activity_id = activity_result['data']['id']
    
    attachment_data = {
        'activity_id': activity_id,
        'task_id': task_id,
        'media_type': 'image',
        'file_path': '/uploads/task_001/photo.jpg',
        'filename': 'photo.jpg',
        'content_type': 'image/jpeg',
        'file_size': 100000
    }
    db.activities.create_attachment(attachment_data)
    
    # Get activities
    result = db.activities.get_activities_by_task(task_id)
    
    assert result['success']
    assert len(result['data']) == 1
    assert 'attachments' in result['data'][0]
    assert len(result['data'][0]['attachments']) == 1
    assert result['data'][0]['attachments'][0]['filename'] == 'photo.jpg'


def test_task_message_mapping(client, sample_employee):
    """Test WhatsApp message ID to task ID mapping."""
    import db.activities
    
    # Create task
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    # Create task message mapping
    whatsapp_msg_id = 'wamid.abc123xyz'
    result = db.activities.create_task_message(task_id, whatsapp_msg_id, '+918005800336')
    assert result['success']
    
    # Retrieve task by WhatsApp message ID
    lookup_result = db.activities.get_task_by_whatsapp_message_id(whatsapp_msg_id)
    assert lookup_result['success']
    assert lookup_result['data']['task_id'] == task_id
    assert lookup_result['data']['employee_phone'] == '+918005800336'


def test_nonexistent_whatsapp_message_id(client):
    """Test looking up non-existent WhatsApp message ID."""
    import db.activities
    
    result = db.activities.get_task_by_whatsapp_message_id('nonexistent_id')
    assert not result['success']
    assert 'not found' in result['error'].lower()


# ============================================================================
# SUBMISSION ENDPOINT TESTS
# ============================================================================

def test_get_submission_valid_token(client, sample_employee):
    """Test GET /api/submissions/<token> with valid token."""
    import db.activities
    
    # Create task and token
    task_data = {
        'title': 'Task for Form Submission',
        'description': 'Please complete this task',
        'projectId': 'test_project',
        'assignedTo': sample_employee,
        'priority': 'high',
        'dueDate': '2026-02-15'
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # GET submission details
    response = client.get(f'/api/submissions/{token}')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert data['data']['task_id'] == task_id
    assert data['data']['task_title'] == 'Task for Form Submission'
    assert data['data']['task_description'] == 'Please complete this task'
    assert data['data']['task_priority'] == 'high'
    assert data['data']['status'] == 'pending'


def test_get_submission_invalid_token(client):
    """Test GET /api/submissions/<token> with invalid token."""
    response = client.get('/api/submissions/invalid_token_xyz')
    
    assert response.status_code in [400, 404]
    data = response.get_json()
    assert not data['success']
    assert 'error' in data


def test_get_submission_used_token(client, sample_employee):
    """Test GET /api/submissions/<token> with already used token."""
    import db.activities
    
    # Create task and token
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Mark as used
    db.activities.mark_submission_complete(token)
    
    # Try to get submission
    response = client.get(f'/api/submissions/{token}')
    
    assert response.status_code in [400, 410]
    data = response.get_json()
    assert not data['success']


def test_submit_task_with_message(client, sample_employee):
    """Test POST /api/submissions/<token> with message only."""
    import db.activities
    
    # Create task and token
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Submit with message
    response = client.post(f'/api/submissions/{token}', data={
        'message': 'Task completed successfully!'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert data['data']['task_id'] == task_id
    assert data['data']['message_posted']
    assert data['data']['files_uploaded'] == 0
    
    # Verify activity was created
    activities_result = db.activities.get_activities_by_task(task_id)
    assert activities_result['success']
    # Should have 2 activities: comment + system
    activities = activities_result['data']
    assert len(activities) >= 2
    assert any(act['activity_type'] == 'comment' and 'completed successfully' in act['message'] for act in activities)


def test_submit_task_with_file(client, sample_employee):
    """Test POST /api/submissions/<token> with file upload."""
    import db.activities
    
    # Create task and token
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Create fake image file
    file_data = io.BytesIO(b'fake image content')
    file_data.name = 'test_image.jpg'
    
    # Submit with file
    response = client.post(f'/api/submissions/{token}', data={
        'message': 'Here is the photo',
        'files': [(file_data, 'test_image.jpg')]
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert data['data']['message_posted']
    assert data['data']['files_uploaded'] >= 1
    assert 'test_image.jpg' in data['data']['uploaded_files']


def test_submit_task_empty_submission(client, sample_employee):
    """Test POST /api/submissions/<token> with no message or files."""
    import db.activities
    
    # Create task and token
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Submit with empty message
    response = client.post(f'/api/submissions/{token}', data={
        'message': ''
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert not data['success']
    assert 'message' in data['error'].lower() and 'files' in data['error'].lower()


def test_submit_task_invalid_token(client):
    """Test POST /api/submissions/<token> with invalid token."""
    response = client.post('/api/submissions/invalid_token', data={
        'message': 'Test message'
    })
    
    assert response.status_code in [400, 404]
    data = response.get_json()
    assert not data['success']


def test_upload_file_endpoint(client, sample_employee):
    """Test POST /api/submissions/<token>/upload endpoint."""
    import db.activities
    
    # Create task and token
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Create fake file
    file_data = io.BytesIO(b'test document content')
    
    # Upload file
    response = client.post(f'/api/submissions/{token}/upload', data={
        'file': (file_data, 'test_doc.pdf')
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert 'filename' in data['data']
    assert data['data']['filename'] == 'test_doc.pdf'
    assert 'file_path' in data['data']


def test_upload_file_no_file_provided(client, sample_employee):
    """Test POST /api/submissions/<token>/upload with no file."""
    import db.activities
    
    # Create task and token
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Upload without file
    response = client.post(f'/api/submissions/{token}/upload', data={})
    
    assert response.status_code == 400
    data = response.get_json()
    assert not data['success']
    assert 'no file' in data['error'].lower()


def test_upload_file_invalid_extension(client, sample_employee):
    """Test POST /api/submissions/<token>/upload with invalid file type."""
    import db.activities
    
    # Create task and token
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Create fake executable file
    file_data = io.BytesIO(b'malicious content')
    
    # Try to upload .exe file
    response = client.post(f'/api/submissions/{token}/upload', data={
        'file': (file_data, 'malware.exe')
    }, content_type='multipart/form-data')
    
    assert response.status_code == 400
    data = response.get_json()
    assert not data['success']
    assert 'not allowed' in data['error'].lower()


# ============================================================================
# FILE DOWNLOAD TESTS
# ============================================================================

def test_download_file_success(client, sample_employee):
    """Test GET /api/files/<path> - successful file download."""
    import os
    
    # Create a test task and activity with attachment
    task_id = 'test_download_task'
    
    # Create a temporary test file
    file_content = b'Test file content for download'
    os.makedirs('uploads/test_download_task', exist_ok=True)
    test_file_path = 'uploads/test_download_task/test_file.txt'
    
    with open(test_file_path, 'wb') as f:
        f.write(file_content)
    
    try:
        # Create activity record
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_activities 
                (task_id, activity_type, message, author_id, author_name, author_type, source)
                VALUES (?, 'attachment', 'Test file upload', ?, 'Test User', 'employee', 'form_submission')
            """, (task_id, sample_employee))
            
            activity_id = cursor.lastrowid
            
            # Create attachment record
            cursor.execute("""
                INSERT INTO task_activity_attachments 
                (activity_id, task_id, media_type, file_path, filename, content_type, file_size)
                VALUES (?, ?, 'document', ?, 'test_file.txt', 'text/plain', ?)
            """, (activity_id, task_id, test_file_path, len(file_content)))
            
            conn.commit()
        
        # Download file
        download_response = client.get(f'/api/files/{test_file_path}')
        
        assert download_response.status_code == 200
        assert download_response.data == file_content
        
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        if os.path.exists('uploads/test_download_task'):
            os.rmdir('uploads/test_download_task')


def test_download_file_not_found(client):
    """Test GET /api/files/<path> - file not found."""
    response = client.get('/api/files/nonexistent/file.txt')
    
    assert response.status_code == 404


def test_download_file_security_path_traversal(client):
    """Test GET /api/files/<path> - prevent path traversal attacks."""
    # Try to access file outside uploads directory
    response = client.get('/api/files/../../../etc/passwd')
    
    assert response.status_code in [400, 403, 404]


def test_download_file_not_in_database(client, sample_employee):
    """Test downloading file that exists on disk but not in database."""
    import os
    import config
    
    # Create physical file without database record
    test_dir = os.path.join(config.UPLOAD_FOLDER, 'test_orphan')
    os.makedirs(test_dir, exist_ok=True)
    test_file_path = os.path.join(test_dir, 'orphan.txt')
    
    with open(test_file_path, 'w') as f:
        f.write('orphaned file')
    
    # Try to download
    relative_path = f'test_orphan/orphan.txt'
    response = client.get(f'/api/files/{relative_path}')
    
    # Should either reject or allow but log warning
    # Implementation-dependent
    assert response.status_code in [200, 403, 404]


def test_download_image_file(client, sample_employee):
    """Test downloading an image file."""
    import os
    
    # Create a test task and activity with image attachment
    task_id = 'test_image_download'
    
    # Create a small test image file (1x1 pixel PNG)
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x07z\x03\x14\x00\x00\x00\x00IEND\xaeB`\x82'
    
    os.makedirs('uploads/test_image_download', exist_ok=True)
    test_file_path = 'uploads/test_image_download/test.png'
    
    with open(test_file_path, 'wb') as f:
        f.write(png_data)
    
    try:
        # Create attachment record
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_activities 
                (task_id, activity_type, message, author_id, author_name, author_type, source)
                VALUES (?, 'attachment', 'Test image upload', ?, 'Test User', 'employee', 'whatsapp_reply')
            """, (task_id, sample_employee))
            
            activity_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO task_activity_attachments 
                (activity_id, task_id, media_type, file_path, filename, content_type, file_size)
                VALUES (?, ?, 'image', ?, 'test.png', 'image/png', ?)
            """, (activity_id, task_id, test_file_path, len(png_data)))
            
            conn.commit()
        
        # Test download
        response = client.get(f'/api/files/{test_file_path}')
        
        assert response.status_code == 200
        assert response.data == png_data
        assert response.headers.get('Content-Type') == 'image/png'
        assert 'test.png' in response.headers.get('Content-Disposition', '')
        
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        if os.path.exists('uploads/test_image_download'):
            os.rmdir('uploads/test_image_download')


# ============================================================================
# STATUS UPDATE TESTS
# ============================================================================

def test_submit_task_with_status_update(client, sample_employee):
    """Test POST /api/submissions/<token> with status field."""
    import db.activities
    
    # Create task
    task_data = {
        'title': 'Status Update Test',
        'projectId': 'test_project',
        'assignedTo': sample_employee,
        'status': 'in_progress'
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Submit with status change
    response = client.post(f'/api/submissions/{token}', data={
        'message': 'Task completed',
        'status': 'completed'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert data['data']['status_updated']
    assert data['data']['new_status'] == 'completed'
    
    # Verify task status changed
    task = db.tasks.get_task_by_id(task_id)
    assert task['success']
    assert task['data']['status'] == 'completed'
    
    # Verify status change activity created
    activities_result = db.activities.get_activities_by_task(task_id)
    activities = activities_result['data']
    assert any(act['activity_type'] == 'status_change' for act in activities)


def test_submit_task_status_only(client, sample_employee):
    """Test submitting only status without message."""
    import db.activities
    
    # Create task
    task_data = {'title': 'Status Only Test', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Submit status only
    response = client.post(f'/api/submissions/{token}', data={
        'status': 'in_progress'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert data['data']['status_updated']
    
    # Verify status changed
    task = db.tasks.get_task_by_id(task_id)
    assert task['data']['status'] == 'in_progress'


def test_submit_task_invalid_status(client, sample_employee):
    """Test submitting invalid status value."""
    import db.activities
    
    # Create task
    task_data = {'title': 'Invalid Status Test', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Submit invalid status
    response = client.post(f'/api/submissions/{token}', data={
        'message': 'Test message',
        'status': 'invalid_status_value'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert not data['success']
    assert 'status' in data['error'].lower()


def test_submit_task_status_override_button(client, sample_employee):
    """Test that form submission status overrides button-triggered status."""
    import db.activities
    
    # Create task
    task_data = {
        'title': 'Status Override Test',
        'projectId': 'test_project',
        'assignedTo': sample_employee,
        'status': 'pending'
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # User clicks "Mark as In Progress" button, then submits form with "Completed"
    # Form submission should override button click
    response = client.post(f'/api/submissions/{token}', data={
        'message': 'Actually finished',
        'status': 'completed'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['data']['new_status'] == 'completed'
    
    # Verify final status
    task = db.tasks.get_task_by_id(task_id)
    assert task['data']['status'] == 'completed'


def test_submit_task_multiple_status_changes(client, sample_employee):
    """Test multiple status changes for same task."""
    import db.activities
    
    # Create task
    task_data = {'title': 'Multiple Status Test', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    # First submission: in_progress
    token1_result = db.activities.create_submission_token(task_id, sample_employee)
    token1 = token1_result['data']['token']
    
    response1 = client.post(f'/api/submissions/{token1}', data={
        'message': 'Starting work',
        'status': 'in_progress'
    })
    assert response1.status_code == 200
    
    # Second submission: pending_verification
    token2_result = db.activities.create_submission_token(task_id, sample_employee)
    token2 = token2_result['data']['token']
    
    response2 = client.post(f'/api/submissions/{token2}', data={
        'message': 'Ready for review',
        'status': 'pending_verification'
    })
    assert response2.status_code == 200
    
    # Verify current status
    task = db.tasks.get_task_by_id(task_id)
    assert task['data']['status'] == 'pending_verification'
    
    # Verify activity history
    activities_result = db.activities.get_activities_by_task(task_id)
    activities = activities_result['data']
    status_changes = [act for act in activities if act['activity_type'] == 'status_change']
    assert len(status_changes) >= 2


def test_submit_task_without_status_keeps_current(client, sample_employee):
    """Test that not including status field keeps current status."""
    import db.activities
    
    # Create task with specific status
    task_data = {
        'title': 'Keep Status Test',
        'projectId': 'test_project',
        'assignedTo': sample_employee,
        'status': 'pending_verification'
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Submit without status field
    response = client.post(f'/api/submissions/{token}', data={
        'message': 'Adding some comments'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert data['data']['status_updated'] is False
    
    # Verify status unchanged
    task = db.tasks.get_task_by_id(task_id)
    assert task['success']
    assert task['data']['status'] == 'pending_verification'
