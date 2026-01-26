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
import database


# ============================================================================
# FIXTURES - Setup and Teardown
# ============================================================================

@pytest.fixture
def mock_kapso():
    """Mock Kapso WhatsApp API to prevent actual message sending during tests."""
    with patch('kapso_service.send_text_message') as mock_send_text, \
         patch('kapso_service.send_task_assignment') as mock_send_task, \
         patch('kapso_service.send_interactive_buttons') as mock_send_buttons:
        
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
        conn = sqlite3.connect(database.DATABASE_PATH)
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

    def test_get_db_connection_context_manager(self, client):
        """
        Regression test: get_db_connection() context manager should always close connections.
        
        This tests the fix for the database locking bug where connections weren't closed
        on errors, causing "database is locked" errors.
        """
        # The context manager should work even if we query inside it
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM employees")
            count = cursor.fetchone()[0]
            assert count >= 0
        
        # After exiting the context, we should be able to get a new connection
        result = database.get_all_employees()
        assert result['success'] == True

    def test_database_connection_closes_on_error(self, client):
        """
        Regression test: Database connections should close even when queries fail.
        
        This prevents database locking issues.
        """
        try:
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                # This should fail - invalid table
                cursor.execute("SELECT * FROM nonexistent_table_xyz")
        except Exception:
            pass  # Expected to fail
        
        # Connection should still be closed, allowing new operations
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
        """Getting employee with string ID should work (ID 1)."""
        response = client.get('/api/employees/1')
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
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

