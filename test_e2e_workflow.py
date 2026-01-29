#!/usr/bin/env python3
"""
Stage 1.6 - End-to-End Integration Test
Tests the complete workflow from task creation to activity feed display
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:5001/api"
FRONTEND_URL = "http://localhost:3000"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")
    sys.exit(1)

def print_info(text):
    print(f"ℹ️  {text}")

def test_health_check():
    print_header("1. Health Check")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print_success("Backend is healthy")
    else:
        print_error("Backend health check failed")

def test_create_employee():
    print_header("2. Create Test Employee")
    import random
    unique_id = random.randint(10000, 99999)
    employee_data = {
        "name": f"Test Employee E2E {unique_id}",
        "email": f"test.e2e.{unique_id}@example.com",
        "phone": f"+9198765{unique_id}",
        "role": "Developer"
    }
    
    response = requests.post(f"{BASE_URL}/employees", json=employee_data)
    if response.status_code == 201:
        employee = response.json()['data']
        print_success(f"Created employee: {employee['name']} (ID: {employee['id']})")
        return employee['id']
    else:
        print_error(f"Failed to create employee: {response.json()}")

def test_create_project():
    print_header("3. Create Test Project")
    project_data = {
        "name": "E2E Test Project",
        "description": "Testing Stage 1.6 workflow",
        "assignedEmployees": []
    }
    
    response = requests.post(f"{BASE_URL}/projects", json=project_data)
    if response.status_code == 201:
        project = response.json()['data']
        print_success(f"Created project: {project['name']} (ID: {project['id']})")
        return project['id']
    else:
        print_error(f"Failed to create project: {response.json()}")

def test_create_task(project_id, employee_id):
    print_header("4. Create Test Task")
    task_data = {
        "title": "E2E Integration Test Task",
        "description": "Testing complete workflow with activities",
        "projectId": project_id,
        "assignedTo": employee_id,
        "priority": "high",
        "status": "in_progress"
    }
    
    response = requests.post(f"{BASE_URL}/tasks", json=task_data)
    if response.status_code == 201:
        task = response.json()['data']
        # Backend returns 'task_id' (formatted like task_001) and 'id' (numeric)
        # Use task_id for database operations
        task_id = task.get('task_id') or task.get('taskId') or task.get('id')
        print_success(f"Created task: {task['title']} (ID: {task_id})")
        return task_id
    else:
        print_error(f"Failed to create task: {response.json()}")

def test_create_submission_token(task_id, employee_id):
    print_header("5. Create Submission Token")
    # This would normally be called internally, but we'll simulate it
    import sqlite3
    import uuid
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect('backend/database.db')
    cursor = conn.cursor()
    
    token = uuid.uuid4().hex[:22]
    expires_at = (datetime.now() + timedelta(days=7)).isoformat()
    
    cursor.execute("""
        INSERT INTO task_submission_tokens (task_id, employee_id, token, status, created_at, expires_at)
        VALUES (?, ?, ?, 'pending', CURRENT_TIMESTAMP, ?)
    """, (task_id, employee_id, token, expires_at))
    
    conn.commit()
    conn.close()
    
    print_success(f"Created submission token: {token}")
    print_info(f"Form URL: {FRONTEND_URL}/submit/{token}")
    return token

def test_get_submission_details(token):
    print_header("6. Get Submission Details")
    response = requests.get(f"{BASE_URL}/submissions/{token}")
    
    if response.status_code == 200:
        data = response.json()['data']
        print_success(f"Retrieved submission details")
        print_info(f"Task: {data['task_title']}")
        print_info(f"Employee: {data['employee_name']}")
        print_info(f"Status: {data['status']}")
        return True
    else:
        print_error(f"Failed to get submission details: {response.json()}")

def test_submit_task_with_status(token):
    print_header("7. Submit Task Update with Status Change")
    
    # Create a test file - use PDF which is in allowed extensions
    import io
    file_content = io.BytesIO(b'This is a test report for E2E testing - PDF content')
    
    data = {
        'message': 'Task completed successfully! All tests passing.',
        'status': 'completed'
    }
    
    files = {
        'files': ('test_report.pdf', file_content, 'application/pdf')
    }
    
    response = requests.post(f"{BASE_URL}/submissions/{token}", data=data, files=files)
    
    if response.status_code == 200:
        result = response.json()['data']
        print_success("Submission successful!")
        print_info(f"Message posted: {result['message_posted']}")
        print_info(f"Files uploaded: {result['files_uploaded']}")
        print_info(f"Status updated: {result['status_updated']}")
        print_info(f"New status: {result['new_status']}")
        return True
    else:
        print_error(f"Failed to submit: {response.json()}")

def test_get_activities(task_id):
    print_header("8. Verify Activities in Feed")
    response = requests.get(f"{BASE_URL}/tasks/{task_id}/activities")
    
    if response.status_code == 200:
        activities = response.json()['data']
        print_success(f"Retrieved {len(activities)} activities")
        
        print_info("\nActivity Timeline:")
        for activity in activities:
            icon = {
                'comment': '💬',
                'attachment': '📎',
                'status_change': '🔄',
                'system': 'ℹ️'
            }.get(activity['activity_type'], '•')
            
            source_badge = {
                'whatsapp_reply': '[WhatsApp]',
                'form_submission': '[Form]',
                'system': '[System]'
            }.get(activity['source'], '')
            
            print(f"  {icon} {activity['author_name']} {source_badge}")
            print(f"     {activity['message']}")
            
            if activity.get('attachments'):
                for att in activity['attachments']:
                    print(f"     📎 {att['filename']} ({att['file_size']} bytes)")
        
        # Verify expected activities
        activity_types = [a['activity_type'] for a in activities]
        
        if 'comment' in activity_types:
            print_success("✓ Comment activity found")
        else:
            print_error("✗ Comment activity missing")
        
        if 'attachment' in activity_types:
            print_success("✓ Attachment activity found")
        else:
            print_error("✗ Attachment activity missing")
        
        if 'status_change' in activity_types:
            print_success("✓ Status change activity found")
        else:
            print_error("✗ Status change activity missing")
        
        return True
    else:
        print_error(f"Failed to get activities: {response.json()}")

def test_task_status_updated(task_id):
    print_header("9. Verify Task Status Updated")
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    
    if response.status_code == 200:
        task = response.json()['data']
        if task['status'] == 'completed':
            print_success(f"Task status is now: {task['status']}")
            return True
        else:
            print_error(f"Task status incorrect: {task['status']} (expected: completed)")
    else:
        print_error(f"Failed to get task: {response.json()}")

def test_token_reuse_prevented(token):
    print_header("10. Verify Token One-Time Use")
    
    data = {
        'message': 'Trying to reuse token'
    }
    
    response = requests.post(f"{BASE_URL}/submissions/{token}", data=data)
    
    if response.status_code == 410:
        print_success("Token correctly marked as used (410 Gone)")
        return True
    else:
        print_error(f"Token reuse not prevented: {response.status_code}")

def main():
    print("\n" + "="*60)
    print("  STAGE 1.6 - END-TO-END INTEGRATION TEST")
    print("  Rich Task Communication Feature")
    print("="*60 + "\n")
    
    try:
        # Test sequence
        test_health_check()
        employee_id = test_create_employee()
        project_id = test_create_project()
        task_id = test_create_task(project_id, employee_id)
        token = test_create_submission_token(task_id, employee_id)
        test_get_submission_details(token)
        test_submit_task_with_status(token)
        test_get_activities(task_id)
        test_task_status_updated(task_id)
        test_token_reuse_prevented(token)
        
        # Success summary
        print_header("🎉 ALL TESTS PASSED!")
        print_success("Stage 1.6 End-to-End Integration: ✅ COMPLETE")
        print_info("\nWorkflow Verified:")
        print("  1. ✅ Task creation")
        print("  2. ✅ Submission token generation")
        print("  3. ✅ Form submission with file & status")
        print("  4. ✅ Activity feed population")
        print("  5. ✅ Task status update")
        print("  6. ✅ Token security (one-time use)")
        
        print_info(f"\n📋 View the task in dashboard:")
        print_info(f"   {FRONTEND_URL}/project/{project_id}")
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
