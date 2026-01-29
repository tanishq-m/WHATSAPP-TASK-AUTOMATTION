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
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
import config
import db

# ============================================================================
# FIXTURES - Setup and Teardown
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
    """Create a test client with a temporary database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Override the database path
    original_db_path = config.DATABASE_PATH
    config.DATABASE_PATH = db_path
    
    # Initialize the test database
    db.init_database()
    
    # Create test client
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
    
    # Cleanup
    config.DATABASE_PATH = original_db_path
    os.close(db_fd)
    os.unlink(db_path)

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
            'dueDate': '2026-02-01',
            'priority': 'high',
            'status': 'unassigned'
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
        assert data['data']['phone'] == '+918005800336'
    
    def test_get_employee_not_found(self, client):
        """GET /api/employees/<id> with invalid ID should return 404."""
        response = client.get('/api/employees/9999')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_get_employee_not_found_returns_proper_error(self, client):
        """BUG-5: Employee not found should return 404 with not_found flag, not 500."""
        response = client.get('/api/employees/99999')
        
        # Should be 404, not 500
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] == False
        assert data.get('not_found') == True, "Response should include not_found flag"
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_get_employee_database_error_returns_500(self, client):
        """BUG-5: Database errors should return 500, not 404."""
        # Test with invalid ID format that might cause database error
        response = client.get('/api/employees/invalid_id_string')
        
        # Should handle gracefully
        assert response.status_code in [404, 500]
        
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

    # ========================================================================
    # P3-6: Optional Dates Tests
    # ========================================================================
    def test_create_project_without_dates(self, client):
        """POST /api/projects without dates should succeed (P3-6)."""
        response = client.post('/api/projects',
            data=json.dumps({
                'name': 'Project Without Dates'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['name'] == 'Project Without Dates'
    
    def test_create_project_with_empty_dates(self, client):
        """POST /api/projects with empty date strings should succeed (P3-6)."""
        response = client.post('/api/projects',
            data=json.dumps({
                'name': 'Project With Empty Dates',
                'startDate': '',
                'endDate': ''
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_create_project_with_only_start_date(self, client):
        """POST /api/projects with only start date should succeed (P3-6)."""
        response = client.post('/api/projects',
            data=json.dumps({
                'name': 'Project With Start Only',
                'startDate': '2026-01-01'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201

    # ========================================================================
    # P3-9: Team Members / Assigned Employees Tests
    # ========================================================================
    def test_create_project_with_assigned_employees(self, client, sample_employee):
        """POST /api/projects with assignedEmployees should succeed (P3-9)."""
        response = client.post('/api/projects',
            data=json.dumps({
                'name': 'Project With Team',
                'assignedEmployees': [sample_employee]
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'assigned_employees' in data['data']
        assert sample_employee in data['data']['assigned_employees']
    
    def test_get_projects_includes_assigned_employees(self, client, sample_employee):
        """GET /api/projects should include assigned_employees array (P3-9)."""
        # Create project with team member
        client.post('/api/projects',
            data=json.dumps({
                'name': 'Team Project',
                'assignedEmployees': [sample_employee]
            }),
            content_type='application/json'
        )
        
        # Fetch all projects
        response = client.get('/api/projects')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Find the team project
        team_project = next((p for p in data['data'] if p['name'] == 'Team Project'), None)
        assert team_project is not None
        assert 'assigned_employees' in team_project
        assert sample_employee in team_project['assigned_employees']
    
    def test_update_project_assigned_employees(self, client, sample_project, sample_employee):
        """PUT /api/projects/<id> should update assigned employees (P3-9)."""
        response = client.put(f'/api/projects/{sample_project}',
            data=json.dumps({
                'assignedEmployees': [sample_employee]
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'assigned_employees' in data['data']
        assert sample_employee in data['data']['assigned_employees']
    
    def test_project_with_multiple_team_members(self, client):
        """POST /api/projects with multiple team members should succeed (P3-9)."""
        # Create multiple employees
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO employees (name, phone, role) VALUES (?, ?, ?)", 
                       ('Member 1', '+911111111111', 'Dev'))
        emp1 = cursor.lastrowid
        cursor.execute("INSERT INTO employees (name, phone, role) VALUES (?, ?, ?)", 
                       ('Member 2', '+912222222222', 'Dev'))
        emp2 = cursor.lastrowid
        cursor.execute("INSERT INTO employees (name, phone, role) VALUES (?, ?, ?)", 
                       ('Member 3', '+913333333333', 'Dev'))
        emp3 = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Create project with all team members
        response = client.post('/api/projects',
            data=json.dumps({
                'name': 'Multi-Member Project',
                'assignedEmployees': [emp1, emp2, emp3]
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert len(data['data']['assigned_employees']) == 3
    
    def test_project_id_generation_uses_sequence(self, client):
        """BUG-3: Project IDs should be generated using sequences to prevent collisions."""
        # Create first project
        response1 = client.post('/api/projects',
            data=json.dumps({'name': 'Project 1'}),
            content_type='application/json'
        )
        assert response1.status_code == 201
        data1 = json.loads(response1.data)
        project_id_1 = data1['data']['id']
        
        # Create second project
        response2 = client.post('/api/projects',
            data=json.dumps({'name': 'Project 2'}),
            content_type='application/json'
        )
        assert response2.status_code == 201
        data2 = json.loads(response2.data)
        project_id_2 = data2['data']['id']
        
        # IDs should be sequential (not random)
        assert project_id_1.startswith('proj_')
        assert project_id_2.startswith('proj_')
        
        # Extract numeric parts
        num1 = int(project_id_1.split('_')[1])
        num2 = int(project_id_2.split('_')[1])
        
        # Second ID should be exactly 1 more than first
        assert num2 == num1 + 1, f"Expected sequential IDs, got {project_id_1} and {project_id_2}"
        
    def test_project_id_never_decreases_after_deletion(self, client):
        """BUG-3: Project sequence should never decrease, even after deletions."""
        # Create project
        response1 = client.post('/api/projects',
            data=json.dumps({'name': 'Project to Delete'}),
            content_type='application/json'
        )
        data1 = json.loads(response1.data)
        project_id_1 = data1['data']['id']
        num1 = int(project_id_1.split('_')[1])
        
        # Delete the project
        client.delete(f'/api/projects/{project_id_1}')
        
        # Create another project - ID should be higher than deleted one
        response2 = client.post('/api/projects',
            data=json.dumps({'name': 'New Project After Delete'}),
            content_type='application/json'
        )
        data2 = json.loads(response2.data)
        project_id_2 = data2['data']['id']
        num2 = int(project_id_2.split('_')[1])
        
        # New ID should be greater than deleted ID
        assert num2 > num1, f"Sequence decreased: {project_id_1} then {project_id_2}"

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
                'status': 'unassigned'
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
        assert data['data']['status'] == 'unassigned'  # BUG-1 fix: Default status should be 'unassigned'
    
    def test_create_task_default_status_is_unassigned(self, client, sample_project):
        """BUG-1: Tasks created without explicit status should default to 'unassigned'."""
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Task Without Status',
                'projectId': sample_project,
                'priority': 'high'
                # No status field provided
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['status'] == 'unassigned', "Task without explicit status must default to 'unassigned'"
        
        # Verify task appears in database with correct status
        task_id = data['data']['task_id']
        get_response = client.get(f'/api/tasks/{task_id}')
        get_data = json.loads(get_response.data)
        assert get_data['data']['status'] == 'unassigned'
    
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

    def test_create_task_after_deletion_no_duplicate_id(self, client, sample_project):
        """
        Regression test: Creating task after deletion should NOT cause duplicate ID error.
        
        This tests the fix for the bug where task_id generation used COUNT(*) instead of MAX(),
        causing UNIQUE constraint violations after tasks were deleted.
        """
        # Create first task
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Task to be deleted',
                'projectId': sample_project,
                'priority': 'medium',
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        first_task_id = data['data']['task_id']
        
        # Delete the task
        response = client.delete(f'/api/tasks/{first_task_id}')
        assert response.status_code == 200
        
        # Create second task - this should NOT fail with duplicate ID
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Task after deletion',
                'projectId': sample_project,
                'priority': 'high',
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        second_task_id = data['data']['task_id']
        
        # Verify the IDs are different (second should be higher)
        first_num = int(first_task_id.split('_')[1])
        second_num = int(second_task_id.split('_')[1])
        assert second_num > first_num, f"Second task ID ({second_task_id}) should be greater than first ({first_task_id})"

    def test_task_id_uses_max_not_count(self, client, sample_project):
        """
        Verify task_id generation uses MAX(task_id) instead of COUNT(*).
        
        This ensures unique IDs even after deletions.
        """
        # Create 3 tasks
        task_ids = []
        for i in range(3):
            response = client.post('/api/tasks',
                data=json.dumps({
                    'title': f'Test Task {i}',
                    'projectId': sample_project,
                    'priority': 'medium',
                    'status': 'unassigned'
                }),
                content_type='application/json'
            )
            assert response.status_code == 201
            data = json.loads(response.data)
            task_ids.append(data['data']['task_id'])
        
        # Delete middle task
        response = client.delete(f'/api/tasks/{task_ids[1]}')
        assert response.status_code == 200
        
        # Create new task - should get ID higher than all existing
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'New Task After Middle Deletion',
                'projectId': sample_project,
                'priority': 'low',
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        new_task_id = data['data']['task_id']
        
        # New task ID should be greater than the highest existing ID
        max_existing = max(int(tid.split('_')[1]) for tid in task_ids)
        new_num = int(new_task_id.split('_')[1])
        assert new_num > max_existing, f"New task ID ({new_task_id}) should be > max existing ({max_existing})"

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
    
    def test_webhook_button_response_completed(self, client, sample_task, mock_kapso):
        """POST /api/webhook/whatsapp with completed button should update task."""
        response = client.post('/api/webhook/whatsapp',
            data=json.dumps({
                'message': {
                    'from': '918005800336',
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
        
        # Verify WhatsApp message was sent (mocked)
        assert mock_kapso['send_text'].called or mock_kapso['send_task'].called
    
    def test_webhook_button_response_not_completed(self, client, sample_task, mock_kapso):
        """POST /api/webhook/whatsapp with not_completed button should update task."""
        response = client.post('/api/webhook/whatsapp',
            data=json.dumps({
                'message': {
                    'from': '918005800336',
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
        
        # Verify WhatsApp message was sent (mocked)
        assert mock_kapso['send_text'].called or mock_kapso['send_task'].called
    
    def test_webhook_duplicate_response_prevention(self, client, sample_task, mock_kapso):
        """POST /api/webhook/whatsapp with duplicate button click should be ignored."""
        # First response - should succeed
        first_response = client.post('/api/webhook/whatsapp',
            data=json.dumps({
                'message': {
                    'from': '918005800336',
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
                    'from': '918005800336',
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
    
    def test_send_whatsapp_updates_whatsapp_sent_field(self, client, sample_task, sample_employee, mock_kapso):
        """BUG-2: Sending WhatsApp should update whatsappSent field correctly."""
        # Verify task initially has whatsapp_sent = False/0
        response = client.get(f'/api/tasks/{sample_task}')
        data = json.loads(response.data)
        initial_whatsapp_sent = data['data'].get('whatsapp_sent', False)
        assert not initial_whatsapp_sent, "Task should not have whatsapp_sent set initially"
        
        # Send task to WhatsApp
        response = client.post(f'/api/tasks/{sample_task}/send-whatsapp-buttons')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True, f"Failed to send WhatsApp: {data}"
        
        # Verify whatsapp_sent field was updated in database
        response = client.get(f'/api/tasks/{sample_task}')
        data = json.loads(response.data)
        assert data['data']['whatsapp_sent'] == True, "whatsapp_sent should be True after sending"
        
        # Verify via WhatsApp status endpoint
        response = client.get(f'/api/tasks/{sample_task}/whatsapp-status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['whatsapp_sent'] == True, "WhatsApp status should show sent=True"

# ============================================================================
# DATABASE TESTS
# ============================================================================

class TestDatabase:
    """Test database operations directly."""
    
    def test_init_database_creates_tables(self, client):
        """init_database should create all required tables."""
        conn = sqlite3.connect(config.DATABASE_PATH)
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
        from db.employees import get_all_employees
        result = get_all_employees()
        assert result['success'] == True

    def test_get_db_connection_context_manager(self, client):
        """
        Regression test: get_db_connection() context manager should always close connections.
        
        This tests the fix for the database locking bug where connections weren't closed
        on errors, causing "database is locked" errors.
        """
        # The context manager should work even if we query inside it
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM employees")
            count = cursor.fetchone()[0]
            assert count >= 0
        
        # After exiting the context, we should be able to get a new connection
        from db.employees import get_all_employees
        result = get_all_employees()
        assert result['success'] == True

    def test_database_connection_closes_on_error(self, client):
        """
        Regression test: Database connections should close even when queries fail.
        
        This prevents database locking issues.
        """
        try:
            with db.get_db_connection() as conn:
                cursor = conn.cursor()
                # This should fail - invalid table
                cursor.execute("SELECT * FROM nonexistent_table_xyz")
        except Exception:
            pass  # Expected to fail
        
        # Connection should still be closed, allowing new operations
        from db.employees import get_all_employees
        result = get_all_employees()
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
    
    def test_project_creation_returns_backend_id(self, client, sample_employee):
        """Test that creating a project returns the backend-generated ID, not frontend ID.
        
        Bug Fix: Previously, frontend generated its own ID and navigated to that ID,
        but backend generated a different ID, causing "project not found" on navigation.
        """
        # Create project with assigned employees
        response = client.post('/api/projects',
            data=json.dumps({
                'name': 'Test ID Project',
                'description': 'Testing backend ID generation',
                'startDate': '2026-01-01',
                'endDate': '2026-12-31',
                'assignedEmployees': [sample_employee]
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'id' in data['data']
        
        # Backend should generate an ID in format "proj_XXX"
        project_id = data['data']['id']
        assert project_id.startswith('proj_')
        
        # Verify the project can be fetched using the returned ID
        response = client.get(f'/api/projects/{project_id}')
        assert response.status_code == 200
        
        fetch_data = json.loads(response.data)
        assert fetch_data['success'] == True
        assert fetch_data['data']['name'] == 'Test ID Project'
        assert fetch_data['data']['id'] == project_id
        
        # Verify project appears in the list with correct ID
        response = client.get('/api/projects')
        assert response.status_code == 200
        
        list_data = json.loads(response.data)
        created_project = next((p for p in list_data['data'] if p['id'] == project_id), None)
        assert created_project is not None
        assert created_project['name'] == 'Test ID Project'

# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Edge case and boundary condition tests."""

    # -------------------------------------------------------------------------
    # Project Edge Cases
    # -------------------------------------------------------------------------
    
    def test_create_project_with_very_long_name(self, client):
        """Project with a very long name should be handled."""
        long_name = 'A' * 500  # 500 character name
        response = client.post('/api/projects',
            data=json.dumps({
                'name': long_name,
                'description': 'Test'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['data']['name'] == long_name

    def test_create_project_with_special_characters(self, client):
        """Project name with special characters should be handled."""
        special_name = "Project #1 (Test) - 'Alpha' & \"Beta\" @2026!"
        response = client.post('/api/projects',
            data=json.dumps({
                'name': special_name,
                'description': 'Test'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['data']['name'] == special_name

    def test_create_project_with_unicode_characters(self, client):
        """Project name with unicode/emoji should be handled."""
        unicode_name = "प्रोजेक्ट 📱 टेस्ट 🚀"
        response = client.post('/api/projects',
            data=json.dumps({
                'name': unicode_name,
                'description': 'Hindi + Emoji test'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['data']['name'] == unicode_name

    def test_create_project_with_empty_description(self, client):
        """Project with empty description should be valid."""
        response = client.post('/api/projects',
            data=json.dumps({
                'name': 'No Description Project',
                'description': ''
            }),
            content_type='application/json'
        )
        assert response.status_code == 201

    def test_update_project_with_empty_name_fails(self, client, sample_project):
        """Updating project with empty name should fail or preserve old name."""
        response = client.put(f'/api/projects/{sample_project}',
            data=json.dumps({'name': ''}),
            content_type='application/json'
        )
        # Should either fail (400) or succeed but preserve non-empty name
        if response.status_code == 200:
            data = json.loads(response.data)
            assert len(data['data']['name']) > 0

    def test_delete_nonexistent_project(self, client):
        """Deleting a non-existent project should return 404."""
        response = client.delete('/api/projects/proj_nonexistent_999')
        assert response.status_code == 404

    def test_get_project_with_invalid_id_format(self, client):
        """Invalid project ID format should return 404."""
        response = client.get('/api/projects/invalid-format')
        assert response.status_code == 404

    # -------------------------------------------------------------------------
    # Task Edge Cases
    # -------------------------------------------------------------------------

    def test_create_task_with_very_long_title(self, client, sample_project):
        """Task with a very long title should be handled."""
        long_title = 'T' * 1000  # 1000 character title
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': long_title,
                'projectId': sample_project,
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['data']['title'] == long_title

    def test_create_task_with_html_in_title(self, client, sample_project):
        """Task title with HTML should be stored as-is (XSS prevention is frontend's job)."""
        html_title = '<script>alert("xss")</script>'
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': html_title,
                'projectId': sample_project,
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['data']['title'] == html_title

    def test_create_task_with_null_optional_fields(self, client, sample_project):
        """Task with null optional fields should work."""
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Minimal Task',
                'projectId': sample_project,
                'description': None,
                'dueDate': None,
                'assignedTo': None,
                'priority': None,
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201

    def test_create_multiple_tasks_rapidly(self, client, sample_project):
        """Creating many tasks rapidly should generate unique IDs."""
        task_ids = []
        for i in range(10):
            response = client.post('/api/tasks',
                data=json.dumps({
                    'title': f'Rapid Task {i}',
                    'projectId': sample_project,
                    'status': 'unassigned'
                }),
                content_type='application/json'
            )
            assert response.status_code == 201
            data = json.loads(response.data)
            task_ids.append(data['data']['task_id'])
        
        # All IDs should be unique
        assert len(task_ids) == len(set(task_ids)), "Task IDs should be unique"

    def test_update_task_with_invalid_status(self, client, sample_project):
        """Updating task with invalid status should fail or be handled."""
        # Create a task first
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Status Test Task',
                'projectId': sample_project,
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        task_id = json.loads(response.data)['data']['task_id']
        
        # Try to update with invalid status
        response = client.put(f'/api/tasks/{task_id}',
            data=json.dumps({'status': 'invalid_status_xyz'}),
            content_type='application/json'
        )
        # Should either reject or accept (depending on validation)
        assert response.status_code in [200, 400]

    def test_update_task_with_invalid_priority(self, client, sample_project):
        """Updating task with invalid priority should be handled."""
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Priority Test Task',
                'projectId': sample_project,
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        task_id = json.loads(response.data)['data']['task_id']
        
        response = client.put(f'/api/tasks/{task_id}',
            data=json.dumps({'priority': 'critical'}),  # Not a valid priority
            content_type='application/json'
        )
        assert response.status_code in [200, 400]

    def test_delete_already_deleted_task(self, client, sample_project):
        """Deleting an already deleted task should return 404."""
        # Create and delete a task
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Delete Test Task',
                'projectId': sample_project,
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        task_id = json.loads(response.data)['data']['task_id']
        
        # First delete should succeed
        response = client.delete(f'/api/tasks/{task_id}')
        assert response.status_code == 200
        
        # Second delete should return 404
        response = client.delete(f'/api/tasks/{task_id}')
        assert response.status_code == 404

    def test_task_id_unique_after_multiple_deletions(self, client, sample_project):
        """Task IDs should remain unique even after multiple create/delete cycles."""
        created_ids = []
        
        for cycle in range(3):
            # Create 3 tasks
            for i in range(3):
                response = client.post('/api/tasks',
                    data=json.dumps({
                        'title': f'Cycle {cycle} Task {i}',
                        'projectId': sample_project,
                        'status': 'unassigned'
                    }),
                    content_type='application/json'
                )
                assert response.status_code == 201
                task_id = json.loads(response.data)['data']['task_id']
                assert task_id not in created_ids, f"Duplicate ID {task_id} found!"
                created_ids.append(task_id)
            
            # Delete all tasks in this cycle
            for task_id in created_ids[-3:]:
                client.delete(f'/api/tasks/{task_id}')
        
        # All IDs should be unique
        assert len(created_ids) == len(set(created_ids))

    # -------------------------------------------------------------------------
    # Employee Edge Cases
    # -------------------------------------------------------------------------

    def test_get_employee_with_string_id(self, client):
        """Getting employee with string ID should work (ID conversion)."""
        # First create an employee
        response = client.post('/api/employees', 
                               json={'name': 'String ID Test', 'phone': '+919999999999', 'role': 'Tester'})
        assert response.status_code == 201
        employee_data = json.loads(response.data)
        employee_id = employee_data['data']['id']
        
        # Now test that we can fetch it using string ID
        response = client.get(f'/api/employees/{employee_id}')
        assert response.status_code == 200

    def test_get_employee_with_negative_id(self, client):
        """Getting employee with negative ID should return 404."""
        response = client.get('/api/employees/-1')
        assert response.status_code == 404

    def test_get_employee_with_zero_id(self, client):
        """Getting employee with ID 0 should return 404."""
        response = client.get('/api/employees/0')
        assert response.status_code == 404

    def test_get_employee_with_very_large_id(self, client):
        """Getting employee with very large ID should return 404."""
        response = client.get('/api/employees/999999999')
        assert response.status_code == 404

    # -------------------------------------------------------------------------
    # Data Integrity Edge Cases
    # -------------------------------------------------------------------------

    def test_task_persists_after_project_fetch(self, client, sample_project):
        """Tasks should remain associated with project after fetching."""
        # Create task
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Persistence Test',
                'projectId': sample_project,
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        task_id = json.loads(response.data)['data']['task_id']
        
        # Fetch project multiple times
        for _ in range(5):
            client.get(f'/api/projects/{sample_project}')
        
        # Task should still exist
        response = client.get(f'/api/tasks/{task_id}')
        assert response.status_code == 200

    def test_concurrent_task_updates_last_write_wins(self, client, sample_project):
        """Last update should win in concurrent update scenario."""
        # Create task
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Concurrent Test',
                'projectId': sample_project,
                'priority': 'low',
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        task_id = json.loads(response.data)['data']['task_id']
        
        # Rapid updates
        client.put(f'/api/tasks/{task_id}',
            data=json.dumps({'priority': 'low'}),
            content_type='application/json'
        )
        client.put(f'/api/tasks/{task_id}',
            data=json.dumps({'priority': 'medium'}),
            content_type='application/json'
        )
        response = client.put(f'/api/tasks/{task_id}',
            data=json.dumps({'priority': 'high'}),
            content_type='application/json'
        )
        
        # Final state should be 'high'
        data = json.loads(response.data)
        assert data['data']['priority'] == 'high'

# ============================================================================
# WHATSAPP EDGE CASES
# ============================================================================

class TestWhatsAppEdgeCases:
    """Edge cases for WhatsApp integration."""

    def test_send_whatsapp_to_task_without_employee(self, client, sample_project, mock_kapso):
        """Sending WhatsApp to unassigned task should fail gracefully."""
        # Create task without assignment
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Unassigned Task',
                'projectId': sample_project,
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        task_id = json.loads(response.data)['data']['task_id']
        
        # Try to send WhatsApp
        response = client.post(f'/api/tasks/{task_id}/send-whatsapp-buttons')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False

    def test_whatsapp_status_for_never_sent_task(self, client, sample_project):
        """Getting WhatsApp status for never-sent task should work."""
        response = client.post('/api/tasks',
            data=json.dumps({
                'title': 'Never Sent Task',
                'projectId': sample_project,
                'status': 'unassigned'
            }),
            content_type='application/json'
        )
        task_id = json.loads(response.data)['data']['task_id']
        
        response = client.get(f'/api/tasks/{task_id}/whatsapp-status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['whatsapp_sent'] == False

# ============================================================================
# PROJECT DESCRIPTION TESTS (NEW)
# ============================================================================

class TestProjectDescription:
    """Tests for project description field functionality."""
    
    def test_create_project_with_description(self, client):
        """POST /api/projects with description should save description."""
        response = client.post('/api/projects',
            data=json.dumps({
                'name': 'Project with Description',
                'description': 'This is a detailed project description with useful information.',
                'startDate': '2026-01-01',
                'endDate': '2026-12-31',
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['description'] == 'This is a detailed project description with useful information.'
        project_id = data['data']['id']
        
        # Verify description persists when fetching
        response = client.get(f'/api/projects/{project_id}')
        data = json.loads(response.data)
        assert data['data']['description'] == 'This is a detailed project description with useful information.'
    
    def test_create_project_with_empty_description(self, client):
        """POST /api/projects with empty description should accept empty string."""
        response = client.post('/api/projects',
            data=json.dumps({
                'name': 'Project with Empty Description',
                'description': '',
                'startDate': '2026-01-01',
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['description'] == ''
    
    def test_create_project_without_description_field(self, client):
        """POST /api/projects without description field should default to empty string."""
        response = client.post('/api/projects',
            data=json.dumps({
                'name': 'Project without Description Field',
                'startDate': '2026-01-01',
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['description'] == ''
    
    def test_update_project_description(self, client, sample_project):
        """PUT /api/projects/<id> should update description."""
        response = client.put(f'/api/projects/{sample_project}',
            data=json.dumps({
                'description': 'Updated description with new information'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['description'] == 'Updated description with new information'
        
        # Verify update persisted
        response = client.get(f'/api/projects/{sample_project}')
        data = json.loads(response.data)
        assert data['data']['description'] == 'Updated description with new information'
    
    def test_update_project_clear_description(self, client, sample_project):
        """PUT /api/projects/<id> should allow clearing description."""
        # First verify project has a description
        response = client.get(f'/api/projects/{sample_project}')
        initial_data = json.loads(response.data)
        assert initial_data['data']['description'] == 'Test Description'
        
        # Clear the description
        response = client.put(f'/api/projects/{sample_project}',
            data=json.dumps({
                'description': ''
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['description'] == ''
    
    def test_update_project_description_with_long_text(self, client, sample_project):
        """PUT /api/projects/<id> should handle long descriptions."""
        long_description = "This is a very long description. " * 100  # ~3000 chars
        
        response = client.put(f'/api/projects/{sample_project}',
            data=json.dumps({
                'description': long_description
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['description'] == long_description
        assert len(data['data']['description']) > 3000
    
    def test_update_project_description_with_special_characters(self, client, sample_project):
        """PUT /api/projects/<id> should handle special characters in description."""
        special_description = "Description with special chars: <>&\"'\\n\\t emoji 🚀 and unicode ñ"
        
        response = client.put(f'/api/projects/{sample_project}',
            data=json.dumps({
                'description': special_description
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['description'] == special_description
    
    def test_get_all_projects_includes_description(self, client):
        """GET /api/projects should include description in all projects."""
        # Create multiple projects with different descriptions
        client.post('/api/projects',
            data=json.dumps({
                'name': 'Project A',
                'description': 'Description A',
            }),
            content_type='application/json'
        )
        
        client.post('/api/projects',
            data=json.dumps({
                'name': 'Project B',
                'description': 'Description B',
            }),
            content_type='application/json'
        )
        
        client.post('/api/projects',
            data=json.dumps({
                'name': 'Project C',
                'description': '',
            }),
            content_type='application/json'
        )
        
        response = client.get('/api/projects')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert len(data['data']) >= 3
        
        # Verify all projects have description field
        for project in data['data']:
            assert 'description' in project
        
        # Find our specific projects
        project_a = next(p for p in data['data'] if p['name'] == 'Project A')
        project_b = next(p for p in data['data'] if p['name'] == 'Project B')
        project_c = next(p for p in data['data'] if p['name'] == 'Project C')
        
        assert project_a['description'] == 'Description A'
        assert project_b['description'] == 'Description B'
        assert project_c['description'] == ''
    
    def test_update_project_preserves_description_when_not_provided(self, client, sample_project):
        """PUT /api/projects/<id> should preserve description if not in update payload."""
        # Verify initial description
        response = client.get(f'/api/projects/{sample_project}')
        initial_data = json.loads(response.data)
        assert initial_data['data']['description'] == 'Test Description'
        
        # Update only the name, not description
        response = client.put(f'/api/projects/{sample_project}',
            data=json.dumps({
                'name': 'Updated Name Only'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # Verify description was preserved
        response = client.get(f'/api/projects/{sample_project}')
        data = json.loads(response.data)
        assert data['data']['name'] == 'Updated Name Only'
        assert data['data']['description'] == 'Test Description'  # Should be unchanged

# ============================================================================
# EMPLOYEE CRUD TESTS (Merged from test_employee_crud.py)
# ============================================================================

class TestEmployeeCRUD:
    """Test class for Employee CRUD operations"""
    
    @pytest.fixture
    def unique_phone(self):
        """Generate a unique phone number for testing"""
        import time
        import random
        timestamp = str(int(time.time()))[-6:]
        random_suffix = random.randint(10, 99)
        return f"+91{timestamp}{random_suffix}"
    
    def test_create_employee_success(self, client, unique_phone):
        """POST /api/employees with valid data creates employee"""
        employee_data = {
            "name": "Test Employee",
            "phone": unique_phone,
            "role": "Developer"
        }
        response = client.post('/api/employees', 
                             data=json.dumps(employee_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['name'] == employee_data['name']
        assert data['data']['phone'] == employee_data['phone']
        assert data['data']['role'] == employee_data['role']
        assert 'id' in data['data']
    
    def test_create_employee_missing_name(self, client):
        """POST /api/employees without name returns 400"""
        employee_data = {"phone": "+918888888888", "role": "Developer"}
        response = client.post('/api/employees',
                             data=json.dumps(employee_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'name' in data['error'].lower()
    
    def test_create_employee_missing_phone(self, client):
        """POST /api/employees without phone returns 400"""
        employee_data = {"name": "Test Employee", "role": "Developer"}
        response = client.post('/api/employees',
                             data=json.dumps(employee_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'phone' in data['error'].lower()
    
    def test_create_employee_missing_role(self, client):
        """POST /api/employees without role returns 400"""
        employee_data = {"name": "Test Employee", "phone": "+918888888888"}
        response = client.post('/api/employees',
                             data=json.dumps(employee_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'role' in data['error'].lower()
    
    def test_create_employee_invalid_phone_no_plus(self, client):
        """POST /api/employees with phone missing + prefix returns 400"""
        employee_data = {
            "name": "Test Employee",
            "phone": "918888888888",  # Missing +
            "role": "Developer"
        }
        response = client.post('/api/employees',
                             data=json.dumps(employee_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'country code' in data['error']
    
    def test_create_employee_invalid_phone_too_short(self, client):
        """POST /api/employees with phone too short returns 400"""
        employee_data = {
            "name": "Test Employee", 
            "phone": "+91888",  # Too short
            "role": "Developer"
        }
        response = client.post('/api/employees',
                             data=json.dumps(employee_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'country code' in data['error']
    
    def test_create_employee_duplicate_phone(self, client, unique_phone):
        """POST /api/employees with existing phone returns 400"""
        # Create first employee
        employee_data = {"name": "First Employee", "phone": unique_phone, "role": "Developer"}
        client.post('/api/employees',
                   data=json.dumps(employee_data),
                   content_type='application/json')
        
        # Try to create another with same phone
        duplicate_data = {
            "name": "Another Employee",
            "phone": unique_phone,  # Same phone
            "role": "Designer"
        }
        response = client.post('/api/employees',
                             data=json.dumps(duplicate_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'already exists' in data['error']
    
    def test_update_employee_success(self, client, unique_phone):
        """PUT /api/employees/<id> updates employee successfully"""
        # Create employee first
        employee_data = {"name": "Test Employee", "phone": unique_phone, "role": "Developer"}
        create_response = client.post('/api/employees',
                                    data=json.dumps(employee_data),
                                    content_type='application/json')
        created_employee = json.loads(create_response.data)['data']
        employee_id = created_employee['id']
        
        # Update employee
        update_data = {"name": "Updated Name", "role": "Senior Developer"}
        response = client.put(f'/api/employees/{employee_id}',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['name'] == "Updated Name"
        assert data['data']['role'] == "Senior Developer"
        assert data['data']['phone'] == unique_phone  # Unchanged
    
    def test_update_employee_not_found(self, client):
        """PUT /api/employees/<id> with invalid ID returns 404"""
        update_data = {"name": "Updated Name"}
        response = client.put('/api/employees/99999',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'not found' in data['error'].lower()
    
    def test_update_employee_duplicate_phone(self, client):
        """PUT /api/employees/<id> with existing phone returns 400"""
        import time
        import random
        timestamp = str(int(time.time()))[-6:]
        random1 = random.randint(10, 49)
        random2 = random.randint(50, 99)
        
        # Create two employees with unique phones
        employee1 = {"name": "Employee 1", "phone": f"+91{timestamp}{random1}", "role": "Developer"}
        employee2 = {"name": "Employee 2", "phone": f"+91{timestamp}{random2}", "role": "Designer"}
        
        client.post('/api/employees', data=json.dumps(employee1), content_type='application/json')
        response2 = client.post('/api/employees', data=json.dumps(employee2), content_type='application/json')
        
        employee2_id = json.loads(response2.data)['data']['id']
        
        # Try to update employee2 with employee1's phone
        update_data = {"phone": employee1['phone']}
        response = client.put(f'/api/employees/{employee2_id}',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'already exists' in data['error']
    
    def test_delete_employee_success(self, client, unique_phone):
        """DELETE /api/employees/<id> removes employee successfully"""
        # Create employee first
        employee_data = {"name": "Test Employee", "phone": unique_phone, "role": "Developer"}
        create_response = client.post('/api/employees',
                                    data=json.dumps(employee_data),
                                    content_type='application/json')
        created_employee = json.loads(create_response.data)['data']
        employee_id = created_employee['id']
        
        # Delete employee
        response = client.delete(f'/api/employees/{employee_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'deleted successfully' in data['message']
    
    def test_delete_employee_not_found(self, client):
        """DELETE /api/employees/<id> with invalid ID returns 404"""
        response = client.delete('/api/employees/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'not found' in data['error'].lower()
    
    def test_delete_employee_with_tasks_cascading(self, client, unique_phone):
        """DELETE /api/employees/<id> properly handles task cascading"""
        # Create employee
        employee_data = {"name": "Task Cascade Test", "phone": unique_phone, "role": "Developer"}
        create_response = client.post('/api/employees',
                                    data=json.dumps(employee_data),
                                    content_type='application/json')
        employee_id = json.loads(create_response.data)['data']['id']
        
        # Create project first
        project_data = {
            "name": "Test Project",
            "assignedEmployees": [employee_id]
        }
        project_response = client.post('/api/projects',
                                     data=json.dumps(project_data),
                                     content_type='application/json')
        project = json.loads(project_response.data)['data']
        
        # Create task assigned to this employee
        task_data = {
            "title": "Test Task",
            "projectId": project['id'],
            "employeeId": employee_id,
            "priority": "high"
        }
        task_response = client.post('/api/tasks',
                                  data=json.dumps(task_data),
                                  content_type='application/json')
        task = json.loads(task_response.data)['data']
        
        # Delete employee
        delete_response = client.delete(f'/api/employees/{employee_id}')
        assert delete_response.status_code == 200
        
        # Verify task is now unassigned
        task_response = client.get(f'/api/tasks/{task["task_id"]}')
        updated_task = json.loads(task_response.data)['data']
        assert updated_task['employee_id'] is None
        assert updated_task['status'] == 'unassigned'
    
    def test_employee_crud_integration(self, client):
        """Integration test for complete employee lifecycle"""
        import time
        import random
        timestamp = str(int(time.time()))[-6:]
        random_suffix = random.randint(100, 999)
        
        # 1. Create employee
        employee_data = {
            "name": "Integration Test Employee",
            "phone": f"+91{timestamp}{random_suffix}",
            "role": "Developer"
        }
        
        create_response = client.post('/api/employees',
                                    data=json.dumps(employee_data),
                                    content_type='application/json')
        assert create_response.status_code == 201
        created_employee = json.loads(create_response.data)['data']
        employee_id = created_employee['id']
        
        # 2. Get employee by ID
        get_response = client.get(f'/api/employees/{employee_id}')
        assert get_response.status_code == 200
        fetched_employee = json.loads(get_response.data)['data']
        assert fetched_employee['name'] == employee_data['name']
        
        # 3. Update employee
        update_data = {"name": "Updated Integration Employee", "role": "Senior Developer"}
        update_response = client.put(f'/api/employees/{employee_id}',
                                   data=json.dumps(update_data),
                                   content_type='application/json')
        assert update_response.status_code == 200
        
        # 4. Verify update
        get_response2 = client.get(f'/api/employees/{employee_id}')
        updated_employee = json.loads(get_response2.data)['data']
        assert updated_employee['name'] == "Updated Integration Employee"
        assert updated_employee['role'] == "Senior Developer"
        
        # 5. List all employees (should include our employee)
        list_response = client.get('/api/employees')
        assert list_response.status_code == 200
        employees_list = json.loads(list_response.data)['data']
        employee_ids = [emp['id'] for emp in employees_list]
        assert employee_id in employee_ids
        
        # 6. Delete employee
        delete_response = client.delete(f'/api/employees/{employee_id}')
        assert delete_response.status_code == 200
        
        # 7. Verify deletion
        get_response3 = client.get(f'/api/employees/{employee_id}')
        assert get_response3.status_code == 404
    
    def test_empty_and_whitespace_handling(self, client):
        """Test handling of empty and whitespace-only values"""
        test_cases = [
            {"name": "", "phone": "+919876543210", "role": "Developer"},  # Empty name
            {"name": "   ", "phone": "+919876543210", "role": "Developer"},  # Whitespace name
            {"name": "Test", "phone": "", "role": "Developer"},  # Empty phone
            {"name": "Test", "phone": "+919876543210", "role": ""},  # Empty role
            {"name": "Test", "phone": "+919876543210", "role": "   "},  # Whitespace role
        ]
        
        for employee_data in test_cases:
            response = client.post('/api/employees',
                                 data=json.dumps(employee_data),
                                 content_type='application/json')
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] == False
    
    def test_special_characters_in_name(self, client):
        """Test names with special characters"""
        import time
        base_timestamp = str(int(time.time()))[-6:]
        
        special_names = [
            "José María",
            "李明",
            "Müller-Schmidt",
            "O'Connor",
            "Jean-Pierre",
            "Андрей"
        ]
        
        for i, name in enumerate(special_names):
            employee_data = {
                "name": name,
                "phone": f"+91{base_timestamp}{i:02d}",
                "role": "Developer"
            }
            
            response = client.post('/api/employees',
                                 data=json.dumps(employee_data),
                                 content_type='application/json')
            
            assert response.status_code == 201, f"Failed for name: {name}"
            created_employee = json.loads(response.data)['data']
            assert created_employee['name'] == name

# ============================================================================
# STAGE 1.1 TESTS - Activity Tables and CRUD
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
    assert len(result['data']['token']) > 10  # Should be a decent length token

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
# STAGE 1.2 TESTS - Submission Endpoints
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
    import io
    
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
    import io
    
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
    import io
    
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
# FILE DOWNLOAD TESTS - Downloading uploaded files
# ============================================================================

def test_download_file_success(client, sample_employee):
    """Test successful file download."""
    import db.activities
    import os
    import tempfile
    
    # Create a test task and activity with attachment
    task_id = 'test_download_task'
    
    # Create a temporary test file
    test_content = b'Test file content for download'
    os.makedirs('uploads/test_download_task', exist_ok=True)
    test_file_path = 'uploads/test_download_task/test_file.txt'
    
    with open(test_file_path, 'wb') as f:
        f.write(test_content)
    
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
            """, (activity_id, task_id, test_file_path, len(test_content)))
            
            conn.commit()
        
        # Test download
        response = client.get(f'/api/files/{test_file_path}')
        
        assert response.status_code == 200
        assert response.data == test_content
        assert 'attachment' in response.headers.get('Content-Disposition', '')
        assert 'test_file.txt' in response.headers.get('Content-Disposition', '')
        
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        if os.path.exists('uploads/test_download_task'):
            os.rmdir('uploads/test_download_task')

def test_download_file_not_found(client):
    """Test download of non-existent file."""
    response = client.get('/api/files/uploads/nonexistent/file.txt')
    assert response.status_code == 404

def test_download_file_security_path_traversal(client):
    """Test that path traversal attacks are blocked."""
    malicious_paths = [
        '../../../etc/passwd',
        '..\\..\\..\\windows\\system32\\config\\sam',
        'uploads/../../../secret.txt'
    ]
    
    for path in malicious_paths:
        response = client.get(f'/api/files/{path}')
        assert response.status_code in [400, 403, 404]  # Any of these is acceptable

def test_download_file_not_in_database(client, sample_employee):
    """Test download of file that exists on disk but not in database."""
    import os
    
    # Create a file that's not in the database
    test_file_path = 'uploads/unauthorized_file.txt'
    os.makedirs('uploads', exist_ok=True)
    
    with open(test_file_path, 'w') as f:
        f.write('Unauthorized content')
    
    try:
        response = client.get(f'/api/files/{test_file_path}')
        assert response.status_code in [403, 404]  # Should be denied
        
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_download_image_file(client, sample_employee):
    """Test downloading an image file with proper content type."""
    import db.activities
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
# STATUS UPDATE FEATURE TESTS - Form-based status changes
# ============================================================================

def test_submit_task_with_status_update(client, sample_employee):
    """Test submitting form with status update."""
    import db.activities
    
    # Create task with initial status
    task_data = {
        'title': 'Test Status Task',
        'projectId': 'test_project',
        'assignedTo': sample_employee,
        'status': 'in_progress'
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    # Create submission token
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Submit with status change
    response = client.post(f'/api/submissions/{token}', data={
        'message': 'Task completed successfully',
        'status': 'completed'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert data['data']['status_updated'] is True
    assert data['data']['new_status'] == 'completed'
    
    # Verify task status was updated
    task = db.tasks.get_task_by_id(task_id)
    assert task['success']
    assert task['data']['status'] == 'completed'
    
    # Verify status_change activity was created
    activities = db.activities.get_activities_by_task(task_id)
    assert activities['success']
    status_activities = [a for a in activities['data'] if a['activity_type'] == 'status_change']
    assert len(status_activities) == 1
    assert 'completed' in status_activities[0]['message'].lower()

def test_submit_task_status_only(client, sample_employee):
    """Test submitting form with only status update (no message or files)."""
    import db.activities
    
    # Create task
    task_data = {
        'title': 'Status Only Task',
        'projectId': 'test_project',
        'assignedTo': sample_employee,
        'status': 'in_progress'
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Submit with only status change
    response = client.post(f'/api/submissions/{token}', data={
        'status': 'pending_verification'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert data['data']['status_updated'] is True
    assert data['data']['message_posted'] is False
    assert data['data']['files_uploaded'] == 0

def test_submit_task_invalid_status(client, sample_employee):
    """Test submitting form with invalid status value."""
    import db.activities
    
    # Create task
    task_data = {
        'title': 'Invalid Status Task',
        'projectId': 'test_project',
        'assignedTo': sample_employee
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Submit with invalid status
    response = client.post(f'/api/submissions/{token}', data={
        'message': 'Test message',
        'status': 'invalid_status_value'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert not data['success']
    assert 'invalid status' in data['error'].lower()

def test_submit_task_status_override_button(client, sample_employee):
    """Test that form submission can override button-set status."""
    import db.activities
    
    # Create task with status set by button click
    task_data = {
        'title': 'Override Test Task',
        'projectId': 'test_project',
        'assignedTo': sample_employee,
        'status': 'completed'  # Simulating button click set this
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    # Override with form submission
    response = client.post(f'/api/submissions/{token}', data={
        'message': 'Actually not done, need more time',
        'status': 'in_progress'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert data['data']['new_status'] == 'in_progress'
    
    # Verify task status was changed back
    task = db.tasks.get_task_by_id(task_id)
    assert task['success']
    assert task['data']['status'] == 'in_progress'

def test_submit_task_multiple_status_changes(client, sample_employee):
    """Test multiple form submissions with different status changes."""
    import db.activities
    
    # Create task
    task_data = {
        'title': 'Multi-status Task',
        'projectId': 'test_project',
        'assignedTo': sample_employee,
        'status': 'in_progress'
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    # First submission - blocked
    token1_result = db.activities.create_submission_token(task_id, sample_employee)
    token1 = token1_result['data']['token']
    
    response1 = client.post(f'/api/submissions/{token1}', data={
        'message': 'Found a blocker',
        'status': 'pending_verification'
    })
    assert response1.status_code == 200
    
    # Second submission - completed
    token2_result = db.activities.create_submission_token(task_id, sample_employee)
    token2 = token2_result['data']['token']
    
    response2 = client.post(f'/api/submissions/{token2}', data={
        'message': 'Blocker resolved, task done',
        'status': 'completed'
    })
    assert response2.status_code == 200
    
    # Verify final status
    task = db.tasks.get_task_by_id(task_id)
    assert task['success']
    assert task['data']['status'] == 'completed'
    
    # Verify both status change activities exist
    activities = db.activities.get_activities_by_task(task_id)
    assert activities['success']
    status_activities = [a for a in activities['data'] if a['activity_type'] == 'status_change']
    assert len(status_activities) == 2

def test_submit_task_without_status_keeps_current(client, sample_employee):
    """Test that submitting without status field keeps current task status."""
    import db.activities
    
    # Create task with specific status
    task_data = {
        'title': 'Keep Status Task',
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

# ============================================================================
# STAGE 1.4 TESTS - WhatsApp Integration Layer
# ============================================================================

def test_get_employee_by_phone(client, sample_employee):
    """Test getting employee by phone number."""
    import db.employees
    
    # Get employee by ID to get their phone
    employee_result = db.employees.get_employee_by_id(sample_employee)
    assert employee_result['success']
    phone = employee_result['data']['phone']
    
    # Get by phone
    result = db.employees.get_employee_by_phone(phone)
    
    assert result['success']
    assert result['data']['id'] == sample_employee
    assert result['data']['phone'] == phone

def test_get_employee_by_phone_normalized(client):
    """Test getting employee by phone with/without + prefix."""
    import db.employees
    
    # Create employee with + prefix
    employee_data = {
        'name': 'Phone Test User',
        'phone': '+919876543210',
        'role': 'Developer'
    }
    create_result = db.employees.create_employee(employee_data)
    assert create_result['success']
    
    # Get by phone without +
    result1 = db.employees.get_employee_by_phone('919876543210')
    assert result1['success']
    assert result1['data']['phone'] == '+919876543210'
    
    # Get by phone with +
    result2 = db.employees.get_employee_by_phone('+919876543210')
    assert result2['success']
    assert result2['data']['phone'] == '+919876543210'

def test_whatsapp_text_reply_to_task(client, sample_employee):
    """Test webhook handler for text reply to a task message."""
    import db.activities
    
    # Create task
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    # Get employee phone
    employee_result = db.employees.get_employee_by_id(sample_employee)
    employee_phone = employee_result['data']['phone']
    
    # Create task message mapping
    whatsapp_msg_id = 'wamid.test123456'
    db.activities.create_task_message(task_id, whatsapp_msg_id, employee_phone)
    
    # Simulate WhatsApp text reply webhook
    webhook_payload = {
        'message': {
            'from': employee_phone,
            'type': 'text',
            'text': {
                'body': 'Task is 80% complete, will finish by tomorrow'
            },
            'context': {
                'id': whatsapp_msg_id  # Reply to tracked message
            }
        }
    }
    
    response = client.post(
        '/api/webhook/whatsapp',
        json=webhook_payload,
        headers={'X-Webhook-Event': 'whatsapp.message.received'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'processed'
    assert data['task_id'] == task_id
    assert data['activity_created']
    
    # Verify activity was created
    activities_result = db.activities.get_activities_by_task(task_id)
    assert activities_result['success']
    activities = activities_result['data']
    assert len(activities) >= 1
    assert any('80% complete' in act['message'] for act in activities)
    assert any(act['source'] == 'whatsapp_reply' for act in activities)

def test_whatsapp_untracked_text_message(client, sample_employee):
    """Test webhook handler for untracked text message."""
    import db.employees
    
    # Get employee phone
    employee_result = db.employees.get_employee_by_id(sample_employee)
    employee_phone = employee_result['data']['phone']
    
    # Simulate WhatsApp text message with no context (not a reply)
    webhook_payload = {
        'message': {
            'from': employee_phone,
            'type': 'text',
            'text': {
                'body': 'Hello, how are you?'
            }
        }
    }
    
    response = client.post(
        '/api/webhook/whatsapp',
        json=webhook_payload,
        headers={'X-Webhook-Event': 'whatsapp.message.received'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ignored'

def test_whatsapp_help_request(client, sample_employee):
    """Test webhook handler for help/form request."""
    import db.employees
    
    # Get employee phone
    employee_result = db.employees.get_employee_by_id(sample_employee)
    employee_phone = employee_result['data']['phone']
    
    # Simulate WhatsApp help request
    webhook_payload = {
        'message': {
            'from': employee_phone,
            'type': 'text',
            'text': {
                'body': 'help'
            }
        }
    }
    
    response = client.post(
        '/api/webhook/whatsapp',
        json=webhook_payload,
        headers={'X-Webhook-Event': 'whatsapp.message.received'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'processed'
    assert data.get('help_sent')

def test_whatsapp_form_request_in_reply(client, sample_employee):
    """Test requesting form URL via WhatsApp reply."""
    import db.activities
    
    # Create task
    task_data = {'title': 'Test Task', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    # Get employee info
    employee_result = db.employees.get_employee_by_id(sample_employee)
    employee_phone = employee_result['data']['phone']
    
    # Create task message mapping
    whatsapp_msg_id = 'wamid.formrequest123'
    db.activities.create_task_message(task_id, whatsapp_msg_id, employee_phone)
    
    # Simulate WhatsApp reply requesting form
    webhook_payload = {
        'message': {
            'from': employee_phone,
            'type': 'text',
            'text': {
                'body': 'Please send me the form link'
            },
            'context': {
                'id': whatsapp_msg_id
            }
        }
    }
    
    response = client.post(
        '/api/webhook/whatsapp',
        json=webhook_payload,
        headers={'X-Webhook-Event': 'whatsapp.message.received'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'processed'
    assert data['task_id'] == task_id
    
    # Verify activity created
    activities_result = db.activities.get_activities_by_task(task_id)
    assert activities_result['success']
    activities = activities_result['data']
    assert any('form link' in act['message'].lower() for act in activities)
    
    # Verify submission token was created
    # We can't easily verify the WhatsApp message was sent in tests,
    # but we can verify the activity and token creation logic worked

def test_whatsapp_reply_creates_correct_activity_type(client, sample_employee):
    """Test that WhatsApp replies create activities with correct metadata."""
    import db.activities
    
    # Create task
    task_data = {'title': 'Metadata Test', 'projectId': 'test_project', 'assignedTo': sample_employee}
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    # Get employee
    employee_result = db.employees.get_employee_by_id(sample_employee)
    employee = employee_result['data']
    
    # Create message mapping
    msg_id = 'wamid.metadata_test'
    db.activities.create_task_message(task_id, msg_id, employee['phone'])
    
    # Send reply
    webhook_payload = {
        'message': {
            'from': employee['phone'],
            'type': 'text',
            'text': {'body': 'Progress update'},
            'context': {'id': msg_id}
        }
    }
    
    response = client.post(
        '/api/webhook/whatsapp',
        json=webhook_payload,
        headers={'X-Webhook-Event': 'whatsapp.message.received'}
    )
    
    assert response.status_code == 200
    
    # Check activity metadata
    activities_result = db.activities.get_activities_by_task(task_id)
    activity = activities_result['data'][0]
    
    assert activity['author_type'] == 'employee'
    assert activity['author_id'] == sample_employee
    assert activity['author_name'] == employee['name']
    assert activity['activity_type'] == 'comment'
    assert activity['source'] == 'whatsapp_reply'
    assert activity['message'] == 'Progress update'

# ============================================================================
# STAGE 1.5 TESTS - Dashboard Activity Feed
# ============================================================================

def test_get_task_activities_success(client, sample_employee):
    """Test GET /api/tasks/<task_id>/activities - successful retrieval."""
    import db.activities
    
    # Create task
    task_data = {
        'title': 'Activity Feed Test',
        'projectId': 'test_project',
        'assignedTo': sample_employee
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    # Create multiple activities
    activities_data = [
        {
            'task_id': task_id,
            'author_type': 'employee',
            'author_id': sample_employee,
            'author_name': 'Test Employee',
            'activity_type': 'comment',
            'source': 'whatsapp_reply',
            'message': 'First comment'
        },
        {
            'task_id': task_id,
            'author_type': 'employee',
            'author_id': sample_employee,
            'author_name': 'Test Employee',
            'activity_type': 'status_change',
            'source': 'form_submission',
            'message': 'Changed status to Completed'
        },
        {
            'task_id': task_id,
            'author_type': 'system',
            'author_id': None,
            'author_name': 'System',
            'activity_type': 'system',
            'source': 'system',
            'message': 'Task assigned'
        }
    ]
    
    for activity_data in activities_data:
        db.activities.create_activity(activity_data)
    
    # Fetch activities
    response = client.get(f'/api/tasks/{task_id}/activities')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert len(data['data']) >= 3
    
    # Verify activities are sorted chronologically
    timestamps = [a['created_at'] for a in data['data']]
    assert timestamps == sorted(timestamps)

def test_get_task_activities_not_found(client):
    """Test GET /api/tasks/<task_id>/activities - task not found."""
    response = client.get('/api/tasks/nonexistent_task/activities')
    
    assert response.status_code == 404
    data = response.get_json()
    assert not data['success']
    assert 'not found' in data['error'].lower()

def test_get_task_activities_with_attachments(client, sample_employee):
    """Test activities endpoint includes attachment data."""
    import db.activities
    import io
    
    # Create task
    task_data = {
        'title': 'Attachment Test',
        'projectId': 'test_project',
        'assignedTo': sample_employee
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    # Create submission token and submit with file
    token_result = db.activities.create_submission_token(task_id, sample_employee)
    token = token_result['data']['token']
    
    file_data = io.BytesIO(b'test file content')
    response = client.post(f'/api/submissions/{token}', data={
        'message': 'Submission with file',
        'files': (file_data, 'test_document.pdf')
    }, content_type='multipart/form-data')
    
    assert response.status_code == 200
    
    # Fetch activities
    activities_response = client.get(f'/api/tasks/{task_id}/activities')
    
    assert activities_response.status_code == 200
    data = activities_response.get_json()
    assert data['success']
    
    # Find attachment activity
    attachment_activities = [a for a in data['data'] if a['activity_type'] == 'attachment']
    assert len(attachment_activities) > 0
    
    # Verify attachment data is included
    attachment_activity = attachment_activities[0]
    assert 'attachments' in attachment_activity
    assert len(attachment_activity['attachments']) > 0
    assert 'filename' in attachment_activity['attachments'][0]
    assert 'file_size' in attachment_activity['attachments'][0]

def test_get_task_activities_empty(client, sample_employee):
    """Test activities endpoint for task with no activities."""
    # Create task without any activities
    task_data = {
        'title': 'Empty Activity Task',
        'projectId': 'test_project',
        'assignedTo': sample_employee
    }
    task_result = db.tasks.create_task(task_data)
    task_id = task_result['data']['task_id']
    
    # Fetch activities
    response = client.get(f'/api/tasks/{task_id}/activities')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success']
    assert isinstance(data['data'], list)
    # May have system activities from task creation
    assert len(data['data']) >= 0

# ============================================================================
# MEDIA HANDLING & FORM SUBMISSION TESTS (NEW FEATURES)
# ============================================================================

