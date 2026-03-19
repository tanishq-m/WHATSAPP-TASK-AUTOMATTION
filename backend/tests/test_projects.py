"""
Tests for Test Projects
Run with: pytest tests/test_projects.py -v
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
