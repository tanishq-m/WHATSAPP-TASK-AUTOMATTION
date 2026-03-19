"""
Shared fixtures for all tests

This file contains pytest fixtures that are automatically available to all test modules.
Fixtures include: client, mock_kapso, sample_employee, sample_project, sample_task
"""

import pytest
import json
import os
import sys
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
import config
import db


# ============================================================================
# GLOBAL MOCKS - Auto-applied to all tests
# ============================================================================

@pytest.fixture(autouse=True)
def mock_all_kapso_globally():
    """
    CRITICAL: Global mock for ALL Kapso API calls to prevent real WhatsApp messages.
    autouse=True means this applies to EVERY test automatically.
    This protects your Kapso message quota during testing.
    """
    with patch('services.kapso_service.send_text_message') as mock_send_text, \
         patch('services.kapso_service.send_task_assignment') as mock_send_task, \
         patch('services.kapso_service.send_interactive_buttons') as mock_send_buttons:
        
        # Mock successful responses for all Kapso API calls
        mock_send_text.return_value = {"success": True, "data": {"messages": [{"id": "mock_msg_id"}]}}
        mock_send_task.return_value = {"success": True, "data": {"messages": [{"id": "mock_msg_id"}]}}
        mock_send_buttons.return_value = {"success": True, "data": {"messages": [{"id": "mock_msg_id"}]}}
        
        yield


# ============================================================================
# CORE FIXTURES - Available to all test modules
# ============================================================================

@pytest.fixture
def mock_kapso():
    """Mock Kapso WhatsApp API to prevent actual message sending during tests."""
    with patch('services.kapso_service.send_text_message') as mock_send_text, \
         patch('services.kapso_service.send_task_assignment') as mock_send_task, \
         patch('services.kapso_service.send_interactive_buttons') as mock_send_buttons:
        
        # Mock successful responses
        mock_send_text.return_value = {"success": True, "data": {"messages": [{"id": "mock_msg_id"}]}}
        mock_send_task.return_value = {"success": True, "data": {"messages": [{"id": "mock_msg_id"}]}}
        mock_send_buttons.return_value = {"success": True, "data": {"messages": [{"id": "mock_msg_id"}]}}
        
        yield {
            'send_text': mock_send_text,
            'send_task': mock_send_task,
            'send_buttons': mock_send_buttons
        }


@pytest.fixture
def client():
    """Create a test client with a temporary database and uploads folder."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Create a temporary uploads directory
    temp_upload_dir = tempfile.mkdtemp()
    
    # Override the database path
    original_db_path = config.DATABASE_PATH
    config.DATABASE_PATH = db_path
    
    # Override upload directories in services
    import services.clarification_service as clarification_service
    import services.submission_service as submission_service
    
    original_pending_dir = clarification_service.PENDING_UPLOAD_DIR
    original_upload_base = submission_service.UPLOAD_BASE_DIR
    
    clarification_service.PENDING_UPLOAD_DIR = os.path.join(temp_upload_dir, 'pending')
    submission_service.UPLOAD_BASE_DIR = temp_upload_dir
    
    # Add UPLOAD_FOLDER to config for tests
    config.UPLOAD_FOLDER = temp_upload_dir
    
    # Initialize the test database
    db.init_database()
    
    # Create test client
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
    
    # Cleanup
    config.DATABASE_PATH = original_db_path
    clarification_service.PENDING_UPLOAD_DIR = original_pending_dir
    submission_service.UPLOAD_BASE_DIR = original_upload_base
    if hasattr(config, 'UPLOAD_FOLDER'):
        delattr(config, 'UPLOAD_FOLDER')
    
    os.close(db_fd)
    os.unlink(db_path)
    
    # Clean up temporary uploads directory
    import shutil
    if os.path.exists(temp_upload_dir):
        shutil.rmtree(temp_upload_dir)


@pytest.fixture
def sample_employee(client):
    """Create a sample employee for testing."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO employees (name, phone, role, created_at)
        VALUES (?, ?, ?, datetime('now'))
    """, ('Test User', '+918005800336', 'Tester'))
    conn.commit()
    employee_id = cursor.lastrowid
    conn.close()
    return employee_id


@pytest.fixture
def sample_project(client):
    """Create a sample project for testing."""
    response = client.post('/api/projects',
        data=json.dumps({
            'name': 'Test Project',
            'description': 'Test Description',
            'startDate': '2026-01-01',
            'endDate': '2026-12-31',
            'teamMembers': []
        }),
        content_type='application/json'
    )
    data = json.loads(response.data)
    return data['data']['id']


@pytest.fixture
def sample_task(client, sample_project, sample_employee):
    """Create a sample task for testing."""
    response = client.post('/api/tasks',
        data=json.dumps({
            'title': 'Test Task',
            'description': 'Test Description',
            'projectId': sample_project,
            'assignedTo': sample_employee,
            'status': 'ready_to_start'
        }),
        content_type='application/json'
    )
    data = json.loads(response.data)
    # Return task_id field from response
    return data['data']['task_id']


@pytest.fixture
def unique_phone():
    """Generate a unique phone number for testing."""
    import time
    import random
    timestamp = str(int(time.time()))[-6:]
    random_suffix = random.randint(10, 99)
    return f"+91{timestamp}{random_suffix}"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_unique_msg_id(prefix='msg'):
    """Helper to generate unique WhatsApp message IDs."""
    import time
    return f'{prefix}_{int(time.time() * 1000000)}'
