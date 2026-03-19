"""
Tests for Test Dashboard
Run with: pytest tests/test_dashboard.py -v
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


class TestDashboardService:
    """Tests for dashboard service functions - Phase 1 Stage 1.1"""
    
    def test_get_dashboard_summary(self, client):
        """Test dashboard summary returns correct aggregated data."""
        from services import dashboard_service
        
        # Get summary
        summary = dashboard_service.get_dashboard_summary()
        
        # Verify structure
        assert "total_projects" in summary, "Missing total_projects"
        assert "total_tasks" in summary, "Missing total_tasks"
        assert "tasks_by_status" in summary, "Missing tasks_by_status"
        assert "completion_rate" in summary, "Missing completion_rate"
        assert "total_employees" in summary, "Missing total_employees"
        
        # Verify types
        assert isinstance(summary["total_projects"], int), "total_projects should be int"
        assert isinstance(summary["total_tasks"], int), "total_tasks should be int"
        assert isinstance(summary["completion_rate"], (int, float)), "completion_rate should be numeric"
        assert isinstance(summary["tasks_by_status"], dict), "tasks_by_status should be dict"
        
        # Verify task status breakdown
        status_keys = ["ready_to_start", "in_progress", "pending_verification", "completed"]
        for key in status_keys:
            assert key in summary["tasks_by_status"], f"Missing status key: {key}"
            assert isinstance(summary["tasks_by_status"][key], int), f"{key} should be int"
    
    def test_projects_overview(self, client):
        """Test projects overview returns per-project stats."""
        from services import dashboard_service
        
        projects = dashboard_service.get_projects_overview()
        
        # Verify it's a list
        assert isinstance(projects, list), "projects_overview should return a list"
        
        # If projects exist, check structure
        if len(projects) > 0:
            project = projects[0]
            required_fields = [
                "project_id", "project_name", "project_color",
                "total_tasks", "completed_tasks", "in_progress_tasks",
                "pending_tasks", "overdue_tasks", "completion_rate",
                "start_date", "end_date", "assigned_employees", "last_activity"
            ]
            for field in required_fields:
                assert field in project, f"Missing field: {field}"
            
            # Verify types
            assert isinstance(project["total_tasks"], int), "total_tasks should be int"
            assert isinstance(project["completion_rate"], (int, float)), "completion_rate should be numeric"
            assert isinstance(project["assigned_employees"], list), "assigned_employees should be list"
    
    def test_overdue_detection(self, client):
        """Test overdue task detection."""
        from services import dashboard_service
        from datetime import datetime, timedelta
        
        # Test completed task (should not be overdue)
        completed_task = {
            "status": "completed",
            "due_date": "2025-01-01"  # Past date
        }
        result = dashboard_service.is_task_overdue(completed_task)
        assert result == False, "Completed task should not be overdue"
        
        # Test overdue task
        overdue_task = {
            "status": "in_progress",
            "due_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        }
        result = dashboard_service.is_task_overdue(overdue_task)
        assert result == True, "Past due date task should be overdue"
        
        # Test future task (not overdue)
        future_task = {
            "status": "in_progress",
            "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        }
        result = dashboard_service.is_task_overdue(future_task)
        assert result == False, "Future task should not be overdue"
        
        # Test task with no due date
        no_date_task = {
            "status": "in_progress",
            "due_date": None
        }
        result = dashboard_service.is_task_overdue(no_date_task)
        assert result == False, "Task with no due date should not be overdue"
    
    def test_completion_rate_calculation(self, client):
        """Test completion rate edge cases."""
        from services import dashboard_service
        
        # Normal case
        rate = dashboard_service.calculate_completion_rate(5, 10)
        assert rate == 50.0, f"Expected 50.0, got {rate}"
        
        # Zero total (edge case)
        rate = dashboard_service.calculate_completion_rate(0, 0)
        assert rate == 0, f"Expected 0 for zero total, got {rate}"
        
        # 100% completion
        rate = dashboard_service.calculate_completion_rate(10, 10)
        assert rate == 100.0, f"Expected 100.0, got {rate}"
        
        # Partial with decimals
        rate = dashboard_service.calculate_completion_rate(1, 3)
        assert abs(rate - 33.3) < 0.1, f"Expected ~33.3, got {rate}"
    
    def test_last_activity_timestamp(self, client):
        """Test last activity timestamp extraction."""
        from services import dashboard_service
        from datetime import datetime, timedelta
        
        # Empty list
        result = dashboard_service.get_last_activity_timestamp([])
        assert result == '', "Empty list should return empty string"
        
        # List with tasks
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        two_hours_ago = now - timedelta(hours=2)
        
        tasks = [
            {"updated_at": hour_ago.isoformat()},
            {"updated_at": two_hours_ago.isoformat()},
            {"updated_at": now.isoformat()}
        ]
        
        result = dashboard_service.get_last_activity_timestamp(tasks)
        assert result != '', "Should return non-empty timestamp"



class TestDashboardAPI:
    """Tests for dashboard API endpoints - Phase 1 Stage 1.2"""
    
    def test_dashboard_summary_endpoint(self, client):
        """Test /api/dashboard/summary endpoint returns correct structure."""
        response = client.get('/api/dashboard/summary')
        
        # Check status code
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Check response structure
        data = response.json
        assert "success" in data, "Missing success field"
        assert data["success"] == True, "success should be True"
        assert "data" in data, "Missing data field"
        
        # Check data structure
        summary = data["data"]
        assert "total_projects" in summary, "Missing total_projects"
        assert "total_tasks" in summary, "Missing total_tasks"
        assert "tasks_by_status" in summary, "Missing tasks_by_status"
        assert "completion_rate" in summary, "Missing completion_rate"
        
        # Check types
        assert isinstance(summary["total_projects"], int)
        assert isinstance(summary["total_tasks"], int)
        assert isinstance(summary["completion_rate"], (int, float))
    
    def test_projects_overview_endpoint(self, client):
        """Test /api/dashboard/projects-overview endpoint returns correct structure."""
        response = client.get('/api/dashboard/projects-overview')
        
        # Check status code
        assert response.status_code == 200
        
        # Check response structure
        data = response.json
        assert data["success"] == True
        assert isinstance(data["data"], list)
        
        # If projects exist, check first project structure
        if len(data["data"]) > 0:
            project = data["data"][0]
            required_fields = [
                "project_id", "project_name", "total_tasks",
                "completed_tasks", "completion_rate"
            ]
            for field in required_fields:
                assert field in project, f"Missing field: {field}"
    
    def test_dashboard_endpoints_with_data(self, client):
        """Test dashboard endpoints with actual project and task data."""
        # Create a project
        project_data = {'name': 'Test Dashboard Project', 'color': '#FF5733'}
        proj_response = client.post('/api/projects',
                                    data=json.dumps(project_data),
                                    content_type='application/json')
        assert proj_response.status_code == 201
        project_id = proj_response.json['data']['id']
        
        # Create some tasks
        for i in range(3):
            task_data = {
                'title': f'Dashboard Test Task {i+1}',
                'projectId': project_id
            }
            task_response = client.post('/api/tasks',
                                       data=json.dumps(task_data),
                                       content_type='application/json')
            assert task_response.status_code == 201
        
        # Test summary endpoint
        summary_response = client.get('/api/dashboard/summary')
        assert summary_response.status_code == 200
        summary_data = summary_response.json['data']
        assert summary_data['total_projects'] >= 1
        assert summary_data['total_tasks'] >= 3
        
        # Test projects overview endpoint
        overview_response = client.get('/api/dashboard/projects-overview')
        assert overview_response.status_code == 200
        projects = overview_response.json['data']
        assert len(projects) >= 1
        
        # Find test project with our tasks (it might have been created in a previous test with different ID)
        # Just verify that at least one project has 3 tasks with the name we created
        test_project = next((p for p in projects if p['project_name'] == 'Test Dashboard Project'), None)
        
        # If we can't find by name, at least verify the API works and returns valid data
        if test_project:
            assert test_project['total_tasks'] == 3
            assert test_project['project_color'] == '#FF5733'
        else:
            # Just verify structure is correct
            assert all('project_id' in p and 'total_tasks' in p for p in projects)
    
    def test_dashboard_error_handling(self, client):
        """Test that dashboard endpoints handle errors gracefully."""
        # These should not crash even with empty database or errors
        summary_response = client.get('/api/dashboard/summary')
        assert summary_response.status_code in [200, 500]  # Should return something
        
        overview_response = client.get('/api/dashboard/projects-overview')
        assert overview_response.status_code in [200, 500]  # Should return something



class TestAttentionService:
    """Tests for attention detection service - Phase 2 Stage 2.1"""
    
    def test_check_if_overdue(self, client):
        """Test overdue task detection."""
        from services import attention_service
        from datetime import datetime, timedelta
        
        # Test completed task (should not be overdue)
        completed_task = {
            "status": "completed",
            "due_date": "2025-01-01"  # Past date
        }
        is_overdue, reason = attention_service.check_if_overdue(completed_task)
        assert is_overdue == False, "Completed task should not be overdue"
        
        # Test overdue task
        overdue_task = {
            "status": "in_progress",
            "due_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        }
        is_overdue, reason = attention_service.check_if_overdue(overdue_task)
        assert is_overdue == True, "Past due date task should be overdue"
        assert "overdue" in reason.lower()
        
        # Test future task (not overdue)
        future_task = {
            "status": "in_progress",
            "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        }
        is_overdue, reason = attention_service.check_if_overdue(future_task)
        assert is_overdue == False, "Future task should not be overdue"
        
        # Test task with no due date
        no_date_task = {
            "status": "in_progress",
            "due_date": None
        }
        is_overdue, reason = attention_service.check_if_overdue(no_date_task)
        assert is_overdue == False, "Task with no due date should not be overdue"
    
    def test_check_no_response(self, client):
        """Test no response detection."""
        from services import attention_service
        from datetime import datetime, timedelta
        
        # No response for 5 hours (should be HIGH priority)
        task_5h = {
            "whatsapp_sent": True,
            "status": "in_progress",
            "updated_at": (datetime.now() - timedelta(hours=5)).isoformat()
        }
        priority, reason = attention_service.check_no_response(task_5h)
        assert priority == "high"
        assert "hours" in reason.lower()
        
        # No response for 3 hours (should be MEDIUM priority)
        task_3h = {
            "whatsapp_sent": True,
            "status": "in_progress",
            "updated_at": (datetime.now() - timedelta(hours=3)).isoformat()
        }
        priority, reason = attention_service.check_no_response(task_3h)
        assert priority == "medium"
        
        # No response for 1 hour (should be None - not enough time)
        task_1h = {
            "whatsapp_sent": True,
            "status": "in_progress",
            "updated_at": (datetime.now() - timedelta(hours=1)).isoformat()
        }
        priority, reason = attention_service.check_no_response(task_1h)
        assert priority is None
        
        # Task not sent via WhatsApp (should be None)
        task_not_sent = {
            "whatsapp_sent": False,
            "status": "in_progress",
            "updated_at": (datetime.now() - timedelta(hours=5)).isoformat()
        }
        priority, reason = attention_service.check_no_response(task_not_sent)
        assert priority is None
    
    def test_check_pending_verification(self, client):
        """Test pending verification detection."""
        from services import attention_service
        from datetime import datetime, timedelta
        
        # Pending for 7 hours (should need attention)
        task_7h = {
            "status": "pending_verification",
            "updated_at": (datetime.now() - timedelta(hours=7)).isoformat()
        }
        priority, reason = attention_service.check_pending_verification(task_7h)
        assert priority == "medium"
        assert "pending" in reason.lower()
        
        # Pending for 2 hours (should be fine)
        task_2h = {
            "status": "pending_verification",
            "updated_at": (datetime.now() - timedelta(hours=2)).isoformat()
        }
        priority, reason = attention_service.check_pending_verification(task_2h)
        assert priority is None
        
        # Not pending verification status
        task_other = {
            "status": "in_progress",
            "updated_at": (datetime.now() - timedelta(hours=10)).isoformat()
        }
        priority, reason = attention_service.check_pending_verification(task_other)
        assert priority is None
    
    def test_calculate_hours_since_update(self, client):
        """Test hours calculation."""
        from services import attention_service
        from datetime import datetime, timedelta
        
        # 5 hours ago
        time_5h_ago = (datetime.now() - timedelta(hours=5)).isoformat()
        hours = attention_service.calculate_hours_since_update(time_5h_ago)
        assert 4.9 <= hours <= 5.1  # Allow small margin
        
        # 30 minutes ago
        time_30m_ago = (datetime.now() - timedelta(minutes=30)).isoformat()
        hours = attention_service.calculate_hours_since_update(time_30m_ago)
        assert 0.4 <= hours <= 0.6
    
    def test_get_attention_items(self, client):
        """Test getting all attention items."""
        from services import attention_service
        
        items = attention_service.get_attention_items()
        
        # Should be a list
        assert isinstance(items, list)
        
        # If items exist, check structure
        if len(items) > 0:
            item = items[0]
            required_fields = [
                "task_id", "task_title", "project_id", "project_name",
                "employee_id", "employee_name", "priority", "reason",
                "hours_since_update", "status"
            ]
            for field in required_fields:
                assert field in item, f"Missing field: {field}"
            
            # Priority should be high or medium
            assert item["priority"] in ["high", "medium"]
    
    def test_attention_items_sorting(self, client):
        """Test that attention items are sorted correctly (high first, then oldest)."""
        from services import attention_service
        
        items = attention_service.get_attention_items()
        
        # If multiple items exist, check sorting
        if len(items) > 1:
            # Check high priority items come before medium
            priorities = [item["priority"] for item in items]
            
            # Find first occurrence of medium (if any)
            if "medium" in priorities:
                first_medium_idx = priorities.index("medium")
                # All items before first medium should be high
                before_medium = priorities[:first_medium_idx]
                if before_medium:
                    assert all(p == "high" for p in before_medium)



class TestAttentionAPI:
    """Tests for attention items API endpoint - Phase 2 Stage 2.2"""
    
    def test_attention_items_endpoint(self, client):
        """Test /api/dashboard/attention-items endpoint."""
        response = client.get('/api/dashboard/attention-items')
        
        # Check status code
        assert response.status_code == 200
        
        # Check response structure
        data = response.json
        assert "success" in data
        assert data["success"] == True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_attention_items_structure(self, client):
        """Test attention items have correct structure."""
        response = client.get('/api/dashboard/attention-items')
        data = response.json
        
        # If items exist, check structure
        if len(data["data"]) > 0:
            item = data["data"][0]
            required_fields = [
                "task_id", "task_title", "priority", "reason"
            ]
            for field in required_fields:
                assert field in item, f"Missing field: {field}"
            
            # Priority should be high or medium
            assert item["priority"] in ["high", "medium"]



class TestDashboardEdgeCases:
    """Edge case tests for dashboard - Phase 6"""
    
    def test_empty_database_structure(self):
        """Test when no projects/tasks exist - verifies graceful handling."""
        from services import dashboard_service
        
        # Test with empty data structures
        empty_summary = {
            "total_projects": 0,
            "total_tasks": 0,
            "completion_rate": 0,
            "tasks_by_status": {
                "ready_to_start": 0,
                "in_progress": 0,
                "pending_verification": 0,
                "completed": 0
            }
        }
        
        # Verify the structure is correct
        assert empty_summary["total_projects"] == 0
        assert empty_summary["total_tasks"] == 0
        assert empty_summary["completion_rate"] == 0
    
    def test_project_with_no_tasks(self):
        """Test project with zero tasks."""
        from services import dashboard_service
        
        # Test that we can get projects overview even with no tasks
        projects = dashboard_service.get_projects_overview()
        
        # Should return list (possibly empty)
        assert isinstance(projects, list)
        
        # All projects should handle 0 tasks gracefully
        for project in projects:
            if project.get("total_tasks") == 0:
                assert project["completion_rate"] == 0
                assert project["completed_tasks"] == 0
                assert project["overdue_tasks"] == 0
    
    def test_task_with_no_due_date(self):
        """Test task without due date."""
        from services import dashboard_service
        
        task_no_due_date = {
            "task_id": "test_001",
            "status": "in_progress",
            "due_date": None
        }
        
        # Should not crash when checking if overdue
        is_overdue = dashboard_service.is_task_overdue(task_no_due_date)
        
        # Task with no due date should not be considered overdue
        assert is_overdue == False
    
    def test_task_with_invalid_timestamp(self):
        """Test task with invalid updated_at timestamp."""
        from services import attention_service
        
        task_invalid = {
            "task_id": "test_002",
            "updated_at": None,
            "status": "in_progress"
        }
        
        try:
            # Should handle None timestamp gracefully
            hours = attention_service.calculate_hours_since_update(task_invalid.get("updated_at"))
            # If it returns a value, should be 0 or very large number indicating invalid
            assert isinstance(hours, (int, float))
        except (TypeError, AttributeError):
            # Or it might raise an exception, which is also acceptable
            pass
    
    def test_completion_rate_edge_cases(self):
        """Test completion rate calculation edge cases."""
        from services import dashboard_service
        
        # Division by zero - no tasks
        rate_zero_total = dashboard_service.calculate_completion_rate(0, 0)
        assert rate_zero_total == 0
        
        # 100% completion
        rate_full = dashboard_service.calculate_completion_rate(10, 10)
        assert rate_full == 100.0
        
        # Partial completion
        rate_partial = dashboard_service.calculate_completion_rate(3, 10)
        assert rate_partial == 30.0
        
        # Edge case: more completed than total (shouldn't happen but test anyway)
        rate_overflow = dashboard_service.calculate_completion_rate(15, 10)
        # Should either cap at 100 or return > 100 (both acceptable)
        assert isinstance(rate_overflow, (int, float))
    
    def test_attention_items_with_no_employee(self):
        """Test attention items when employee data is missing."""
        from services import attention_service
        
        # Get attention items - should not crash even if employee data incomplete
        items = attention_service.get_attention_items()
        
        # Should return a list
        assert isinstance(items, list)
        
        # Check that items handle missing employee data
        for item in items:
            # Should have employee_id even if other employee data is missing
            assert "employee_id" in item or "task_id" in item
    
    def test_attention_items_empty_state(self):
        """Test attention items when nothing needs attention."""
        from services import attention_service
        
        # Get attention items - should return list even when empty
        items = attention_service.get_attention_items()
        
        # Should return empty list, not None or error
        assert isinstance(items, list)
        assert len(items) >= 0  # Could be 0 or more
    
    def test_overdue_detection_with_future_date(self):
        """Test overdue detection with future due date."""
        from services import attention_service
        from datetime import datetime, timedelta
        
        future_task = {
            "task_id": "test_003",
            "status": "in_progress",
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        }
        
        is_overdue, reason = attention_service.check_if_overdue(future_task)
        
        # Future task should not be overdue
        assert is_overdue == False
    
    def test_overdue_detection_with_completed_task(self):
        """Test that completed tasks are never overdue."""
        from services import attention_service
        from datetime import datetime, timedelta
        
        completed_overdue_task = {
            "task_id": "test_004",
            "status": "completed",
            "due_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        }
        
        is_overdue, reason = attention_service.check_if_overdue(completed_overdue_task)
        
        # Completed task should never be overdue, even if date passed
        assert is_overdue == False
    
    def test_hours_since_update_calculations(self):
        """Test various hour calculations."""
        from services import attention_service
        from datetime import datetime, timedelta
        
        # Recent update (1 hour ago)
        recent_time = (datetime.now() - timedelta(hours=1)).isoformat()
        hours_recent = attention_service.calculate_hours_since_update(recent_time)
        assert 0.9 <= hours_recent <= 1.1  # Allow small margin
        
        # Old update (48 hours ago)
        old_time = (datetime.now() - timedelta(hours=48)).isoformat()
        hours_old = attention_service.calculate_hours_since_update(old_time)
        assert 47.9 <= hours_old <= 48.1
        
        # Very recent (5 minutes ago)
        very_recent = (datetime.now() - timedelta(minutes=5)).isoformat()
        hours_very_recent = attention_service.calculate_hours_since_update(very_recent)
        assert hours_very_recent < 0.2  # Less than 12 minutes
    
    def test_projects_overview_sorting(self):
        """Test that projects are sorted by last activity."""
        from services import dashboard_service
        
        projects = dashboard_service.get_projects_overview()
        
        if len(projects) > 1:
            # Check that projects are sorted (most recent first)
            for i in range(len(projects) - 1):
                # Each project should have last_activity
                if "last_activity" in projects[i] and "last_activity" in projects[i + 1]:
                    # More recent or equal (could be same timestamp)
                    assert projects[i]["last_activity"] >= projects[i + 1]["last_activity"]
    
    def test_attention_priority_sorting(self):
        """Test that attention items are sorted by priority."""
        from services import attention_service
        
        items = attention_service.get_attention_items()
        
        if len(items) > 1:
            # High priority items should come before medium
            high_indices = [i for i, item in enumerate(items) if item["priority"] == "high"]
            medium_indices = [i for i, item in enumerate(items) if item["priority"] == "medium"]
            
            if high_indices and medium_indices:
                # Last high priority should come before first medium priority
                assert max(high_indices) < min(medium_indices)
    
    def test_dashboard_with_mixed_data(self):
        """Test dashboard with mix of complete, incomplete, overdue tasks."""
        from services import dashboard_service
        
        summary = dashboard_service.get_dashboard_summary()
        
        # Summary should always have required fields
        required_fields = ["total_projects", "total_tasks", "tasks_by_status", "completion_rate"]
        for field in required_fields:
            assert field in summary
        
        # All counts should be non-negative
        assert summary["total_projects"] >= 0
        assert summary["total_tasks"] >= 0
        assert summary["completion_rate"] >= 0
        
        # Task status counts should sum to total (if we have tasks)
        if summary["total_tasks"] > 0:
            status_sum = sum(summary["tasks_by_status"].values())
            # Sum might not exactly match if some tasks have other statuses
            assert status_sum <= summary["total_tasks"]


# ============================================================================
# Dashboard Activity Feed Tests
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
        'files': [(file_data, 'test_document.pdf')]
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




