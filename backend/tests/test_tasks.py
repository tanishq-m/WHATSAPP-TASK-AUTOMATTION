"""
Tests for Test Tasks
Run with: pytest tests/test_tasks.py -v
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
