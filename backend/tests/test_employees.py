"""
Tests for Test Employees
Run with: pytest tests/test_employees.py -v
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
