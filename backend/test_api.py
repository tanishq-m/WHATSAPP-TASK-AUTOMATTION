"""
API Test Suite for WhatsApp Task Manager Backend

Run tests: pytest test_api.py -v
Run with coverage: pytest test_api.py -v --cov=. --cov-report=html

This file tests all API endpoints and database operations.
Add new tests here when adding new functionality.
"""

import pytest
import json
import os
import sys
import tempfile
import sqlite3

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
import database


# ============================================================================
# FIXTURES - Setup and Teardown
# ============================================================================

@pytest.fixture
def client():
    """Create a test client with a temporary database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Override the database path
    original_db_path = database.DATABASE_PATH
    database.DATABASE_PATH = db_path
    
    # Initialize the test database
    database.init_database()
    
    # Create test client
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
    
    # Cleanup
    database.DATABASE_PATH = original_db_path
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def sample_employee(client):
    """Create a sample employee for testing."""
    conn = sqlite3.connect(database.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO employees (name, phone, role, created_at)
        VALUES (?, ?, ?, datetime('now'))
    """, ('Test User', '+911234567890', 'Tester'))
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
            'dueDate': '2026-02-01',
            'priority': 'high',
            'status': 'todo'
        }),
        content_type='application/json'
    )
    data = json.loads(response.data)
    return data['data']['task_id']


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check_returns_ok(self, client):
        """GET /api/health should return healthy status with database check."""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'
        assert 'timestamp' in data


# ============================================================================
# EMPLOYEE TESTS
# ============================================================================

class TestEmployees:
    """Test employee endpoints."""
    
    def test_get_employees_returns_list(self, client, sample_employee):
        """GET /api/employees should return list of employees."""
        response = client.get('/api/employees')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert isinstance(data['data'], list)
        assert len(data['data']) >= 1
    
    def test_get_employee_by_id(self, client, sample_employee):
        """GET /api/employees/<id> should return specific employee."""
        response = client.get(f'/api/employees/{sample_employee}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['name'] == 'Test User'
        assert data['data']['phone'] == '+911234567890'
    
    def test_get_employee_not_found(self, client):
        """GET /api/employees/<id> with invalid ID should return 404."""
        response = client.get('/api/employees/9999')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] == False


# ============================================================================
# PROJECT TESTS
# ============================================================================

class TestProjects:
    """Test project endpoints."""
    
    def test_get_projects_empty(self, client):
        """GET /api/projects should return empty list initially."""
        response = client.get('/api/projects')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert isinstance(data['data'], list)
    
    def test_create_project_success(self, client):
        """POST /api/projects should create a new project."""
        response = client.post('/api/projects',
            data=json.dumps({
                'name': 'New Project',
                'description': 'Project Description',
                'startDate': '2026-01-01',
                'endDate': '2026-06-30',
                'teamMembers': []
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['name'] == 'New Project'
        assert 'id' in data['data']
        assert data['data']['id'].startswith('proj_')
    
    def test_create_project_missing_name(self, client):
        """POST /api/projects without name should fail."""
        response = client.post('/api/projects',
            data=json.dumps({
                'description': 'No name project'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_get_project_by_id(self, client, sample_project):
        """GET /api/projects/<id> should return specific project."""
        response = client.get(f'/api/projects/{sample_project}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['name'] == 'Test Project'
    
    def test_update_project(self, client, sample_project):
        """PUT /api/projects/<id> should update project and return updated data."""
        response = client.put(f'/api/projects/{sample_project}',
            data=json.dumps({
                'name': 'Updated Project Name'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        # Should return the updated project data
        assert 'data' in data
        assert data['data']['name'] == 'Updated Project Name'
    
    def test_delete_project(self, client, sample_project):
        """DELETE /api/projects/<id> should delete project."""
        response = client.delete(f'/api/projects/{sample_project}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Verify project is deleted
        response = client.get(f'/api/projects/{sample_project}')
        assert response.status_code == 404


# ============================================================================
# TASK TESTS
# ============================================================================

class TestTasks:
    """Test task endpoints."""
    
    def test_get_tasks_empty(self, client):
        """GET /api/tasks should return empty list initially."""
        response = client.get('/api/tasks')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert isinstance(data['data'], list)
    
    def test_create_task_success(self, client, sample_project, sample_employee):
        """POST /api/tasks should create a new task."""
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'New Task',
                'description': 'Task Description',
                'projectId': sample_project,
                'assignedTo': sample_employee,
                'dueDate': '2026-03-01',
                'priority': 'medium',
                'status': 'todo'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['title'] == 'New Task'
        assert 'task_id' in data['data']
        assert data['data']['task_id'].startswith('task_')
    
    def test_create_task_missing_title(self, client, sample_project):
        """POST /api/tasks without title should fail."""
        response = client.post('/api/tasks',
            data=json.dumps({
                'description': 'No title task',
                'projectId': sample_project
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'title' in data['error'].lower()
    
    def test_create_task_minimal(self, client, sample_project):
        """POST /api/tasks with only required fields should succeed."""
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Minimal Task',
                'projectId': sample_project
                # No assignedTo, dueDate, priority, status - all optional
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['title'] == 'Minimal Task'
        assert data['data']['priority'] == 'medium'  # Default value
    
    def test_get_task_by_id(self, client, sample_task):
        """GET /api/tasks/<task_id> should return specific task."""
        response = client.get(f'/api/tasks/{sample_task}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['title'] == 'Test Task'
    
    def test_get_tasks_by_project(self, client, sample_task, sample_project):
        """GET /api/tasks?projectId=xxx should filter by project."""
        response = client.get(f'/api/tasks?projectId={sample_project}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert len(data['data']) >= 1
        assert all(t['project_id'] == sample_project for t in data['data'])
    
    def test_update_task(self, client, sample_task):
        """PUT /api/tasks/<task_id> should update task."""
        response = client.put(f'/api/tasks/{sample_task}',
            data=json.dumps({
                'title': 'Updated Task Title',
                'status': 'in_progress'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['title'] == 'Updated Task Title'
        assert data['data']['status'] == 'in_progress'
    
    def test_update_task_priority(self, client, sample_task):
        """PUT /api/tasks/<task_id> should update priority."""
        response = client.put(f'/api/tasks/{sample_task}',
            data=json.dumps({
                'priority': 'low'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['data']['priority'] == 'low'
    
    def test_update_task_not_found(self, client):
        """PUT /api/tasks/<task_id> with invalid ID should return 404."""
        response = client.put('/api/tasks/task_nonexistent',
            data=json.dumps({'title': 'Test'}),
            content_type='application/json'
        )
        assert response.status_code == 404
    
    def test_delete_task(self, client, sample_task):
        """DELETE /api/tasks/<task_id> should delete task."""
        response = client.delete(f'/api/tasks/{sample_task}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Verify task is deleted
        response = client.get(f'/api/tasks/{sample_task}')
        assert response.status_code == 404


# ============================================================================
# WHATSAPP INTEGRATION TESTS
# ============================================================================

class TestWhatsAppIntegration:
    """Test WhatsApp-related endpoints."""
    
    def test_get_whatsapp_status(self, client, sample_task):
        """GET /api/tasks/<task_id>/whatsapp-status should return status."""
        response = client.get(f'/api/tasks/{sample_task}/whatsapp-status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'whatsapp_sent' in data['data']
        assert 'whatsapp_response' in data['data']
    
    def test_whatsapp_status_not_found(self, client):
        """GET /api/tasks/<task_id>/whatsapp-status with invalid ID should return 404."""
        response = client.get('/api/tasks/task_nonexistent/whatsapp-status')
        assert response.status_code == 404
    
    def test_send_whatsapp_task_not_found(self, client):
        """POST /api/tasks/<task_id>/send-whatsapp-buttons with invalid ID should return 404."""
        response = client.post('/api/tasks/task_nonexistent/send-whatsapp-buttons')
        assert response.status_code == 404
    
    def test_send_whatsapp_unassigned_task(self, client, sample_project):
        """POST /api/tasks/<task_id>/send-whatsapp-buttons for unassigned task should return 400."""
        # Create task WITHOUT an employee (now allowed by API)
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Unassigned Task',
                'description': 'No employee assigned',
                'projectId': sample_project
                # Note: assignedTo is not provided
            }),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert data['success'] == True, f"Task creation failed: {data}"
        task_id = data['data']['task_id']
        
        # Try to send unassigned task to WhatsApp - should fail with 400
        response = client.post(f'/api/tasks/{task_id}/send-whatsapp-buttons')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'no assigned employee' in data['error'].lower()
    
    def test_webhook_verification(self, client):
        """GET /api/webhook/whatsapp should return OK for verification."""
        response = client.get('/api/webhook/whatsapp')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
    
    def test_webhook_post_invalid_payload(self, client):
        """POST /api/webhook/whatsapp with invalid payload should handle gracefully."""
        response = client.post('/api/webhook/whatsapp',
            data=json.dumps({'invalid': 'payload'}),
            content_type='application/json'
        )
        # Should return 200 to prevent Kapso retries
        assert response.status_code == 200
    
    def test_webhook_button_response_completed(self, client, sample_task):
        """POST /api/webhook/whatsapp with completed button should update task."""
        response = client.post('/api/webhook/whatsapp',
            data=json.dumps({
                'message': {
                    'from': '911234567890',
                    'interactive': {
                        'type': 'button_reply',
                        'button_reply': {
                            'id': f'completed_{sample_task}',
                            'title': '✅ Yes, Completed'
                        }
                    }
                }
            }),
            content_type='application/json',
            headers={'X-Webhook-Event': 'whatsapp.message.received'}
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'processed'
        
        # Verify task was updated
        response = client.get(f'/api/tasks/{sample_task}/whatsapp-status')
        data = json.loads(response.data)
        assert data['data']['whatsapp_response'] == 'completed'
    
    def test_webhook_button_response_not_completed(self, client, sample_task):
        """POST /api/webhook/whatsapp with not_completed button should update task."""
        response = client.post('/api/webhook/whatsapp',
            data=json.dumps({
                'message': {
                    'from': '911234567890',
                    'interactive': {
                        'type': 'button_reply',
                        'button_reply': {
                            'id': f'not_completed_{sample_task}',
                            'title': '❌ No, Not Yet'
                        }
                    }
                }
            }),
            content_type='application/json',
            headers={'X-Webhook-Event': 'whatsapp.message.received'}
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'processed'
        
        # Verify task was updated but status didn't change to done
        response = client.get(f'/api/tasks/{sample_task}')
        data = json.loads(response.data)
        assert data['data']['status'] != 'done'
    
    def test_webhook_duplicate_response_prevention(self, client, sample_task):
        """POST /api/webhook/whatsapp with duplicate button click should be ignored."""
        # First response - should succeed
        first_response = client.post('/api/webhook/whatsapp',
            data=json.dumps({
                'message': {
                    'from': '911234567890',
                    'interactive': {
                        'type': 'button_reply',
                        'button_reply': {
                            'id': f'completed_{sample_task}',
                            'title': '✅ Yes, Completed'
                        }
                    }
                }
            }),
            content_type='application/json',
            headers={'X-Webhook-Event': 'whatsapp.message.received'}
        )
        assert first_response.status_code == 200
        first_data = json.loads(first_response.data)
        assert first_data['status'] == 'processed'
        
        # Second response (duplicate) - should be ignored
        second_response = client.post('/api/webhook/whatsapp',
            data=json.dumps({
                'message': {
                    'from': '911234567890',
                    'interactive': {
                        'type': 'button_reply',
                        'button_reply': {
                            'id': f'not_completed_{sample_task}',
                            'title': '❌ No, Not Yet'
                        }
                    }
                }
            }),
            content_type='application/json',
            headers={'X-Webhook-Event': 'whatsapp.message.received'}
        )
        assert second_response.status_code == 200
        second_data = json.loads(second_response.data)
        assert second_data['status'] == 'ignored'
        assert second_data['reason'] == 'Task already has a response'
        assert second_data['original_response'] == 'completed'
        assert second_data['attempted_response'] == 'not_completed'
        
        # Verify task still has original response
        response = client.get(f'/api/tasks/{sample_task}')
        data = json.loads(response.data)
        assert data['data']['whatsapp_response'] == 'completed'


# ============================================================================
# DATABASE TESTS
# ============================================================================

class TestDatabase:
    """Test database operations directly."""
    
    def test_init_database_creates_tables(self, client):
        """init_database should create all required tables."""
        conn = sqlite3.connect(database.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        assert 'employees' in tables
        assert 'projects' in tables
        assert 'tasks' in tables
        assert 'project_employees' in tables
    
    def test_database_connection(self, client):
        """Database should be connectable."""
        result = database.get_all_employees()
        assert result['success'] == True


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling."""
    
    def test_404_for_unknown_endpoint(self, client):
        """Unknown endpoints should return 404."""
        response = client.get('/api/unknown/endpoint')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_invalid_json_body(self, client):
        """Invalid JSON should be handled gracefully."""
        response = client.post('/api/projects',
            data='not valid json',
            content_type='application/json'
        )
        # Should return 400 or 500, not crash
        assert response.status_code in [400, 415, 500]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """End-to-end integration tests."""
    
    def test_full_task_lifecycle(self, client, sample_project, sample_employee):
        """Test complete task lifecycle: create -> update -> send -> receive response -> delete."""
        
        # 1. Create task
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Lifecycle Test Task',
                'description': 'Testing full lifecycle',
                'projectId': sample_project,
                'assignedTo': sample_employee,
                'dueDate': '2026-03-01',
                'priority': 'high',
                'status': 'todo'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        task_id = data['data']['task_id']
        
        # 2. Update task status
        response = client.put(f'/api/tasks/{task_id}',
            data=json.dumps({'status': 'in_progress'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # 3. Simulate webhook response
        response = client.post('/api/webhook/whatsapp',
            data=json.dumps({
                'message': {
                    'from': '911234567890',
                    'interactive': {
                        'type': 'button_reply',
                        'button_reply': {
                            'id': f'completed_{task_id}',
                            'title': '✅ Yes, Completed'
                        }
                    }
                }
            }),
            content_type='application/json',
            headers={'X-Webhook-Event': 'whatsapp.message.received'}
        )
        assert response.status_code == 200
        
        # 4. Verify task is marked done
        response = client.get(f'/api/tasks/{task_id}')
        data = json.loads(response.data)
        assert data['data']['status'] == 'done'
        assert data['data']['whatsapp_response'] == 'completed'
        
        # 5. Delete task
        response = client.delete(f'/api/tasks/{task_id}')
        assert response.status_code == 200
        
        # 6. Verify deleted
        response = client.get(f'/api/tasks/{task_id}')
        assert response.status_code == 404


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
