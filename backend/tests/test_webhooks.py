"""
Tests for Test Webhooks
Run with: pytest tests/test_webhooks.py -v
"""

import pytest
import json
import os
import sys
import tempfile
import sqlite3
import time
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
import config
import db


# Helper function (duplicated from conftest for import issues)
def get_unique_msg_id(prefix='msg'):
    """Helper to generate unique WhatsApp message IDs."""
    return f'{prefix}_{int(time.time() * 1000000)}'




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


class TestPhase2WebhookDeduplication:
    """Test suite for webhook deduplication."""
    
    def test_insert_webhook_record(self, client):
        """Test inserting webhook deduplication record."""
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            webhook_id = get_unique_msg_id('webhook')
            
            cursor.execute("""
                INSERT INTO webhook_deduplication
                (webhook_id, webhook_type, phone, payload_hash)
                VALUES (?, ?, ?, ?)
            """, (webhook_id, 'message', '+919876543210', 'hash123'))
            conn.commit()
            
            # Verify
            cursor.execute("""
                SELECT webhook_type, phone 
                FROM webhook_deduplication WHERE webhook_id = ?
            """, (webhook_id,))
            
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 'message'
            assert row[1] == '+919876543210'
    
    def test_duplicate_webhook_detection(self, client):
        """Test detecting duplicate webhooks."""
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            webhook_id = get_unique_msg_id('dup_webhook')
            
            # Insert first webhook
            cursor.execute("""
                INSERT INTO webhook_deduplication
                (webhook_id, webhook_type, phone)
                VALUES (?, ?, ?)
            """, (webhook_id, 'status', '+919876543210'))
            conn.commit()
            
            # Try to insert duplicate (should fail due to UNIQUE constraint)
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute("""
                    INSERT INTO webhook_deduplication
                    (webhook_id, webhook_type, phone)
                    VALUES (?, ?, ?)
                """, (webhook_id, 'status', '+919876543210'))
                conn.commit()



class TestPhase2Stage2WebhookStatusHandlers:
    """Test webhook handlers for message delivery, read, and failure status."""
    
    def _create_task_with_message(self, client, sample_project, sample_employee, task_title='Test Task'):
        """Helper to create a task and message record."""
        task_data = {
            'title': task_title,
            'projectId': sample_project,
            'assignedTo': sample_employee,
            'dueDate': '2025-02-15',
            'status': 'pending'
        }
        
        task_response = client.post('/api/tasks',
                                   data=json.dumps(task_data),
                                   content_type='application/json')
        assert task_response.status_code == 201
        task_id = task_response.json['data']['id']
        
        # Create message record
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT phone FROM employees WHERE id = ?", (sample_employee,))
            emp_phone = cursor.fetchone()['phone']
            
            whatsapp_msg_id = f"wamid.test_{task_id}_assignment"
            
            cursor.execute("""
                INSERT INTO task_messages 
                (task_id, employee_phone, message_type, whatsapp_message_id, sent_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (task_id, emp_phone, 'task_assignment', whatsapp_msg_id))
            
            message_id = cursor.lastrowid
            conn.commit()
        
        return task_id, whatsapp_msg_id, message_id
    
    def test_webhook_delivery_status_update(self, client, sample_project, sample_employee, mock_kapso):
        """Test delivery status webhook updates message."""
        task_id, whatsapp_msg_id, _ = self._create_task_with_message(
            client, sample_project, sample_employee
        )
        # Send delivery status webhook
        webhook_payload = {
            'statuses': [{
                'id': whatsapp_msg_id,
                'status': 'delivered',
                'timestamp': '1706500000',
                'recipient_id': '918005800336'
            }]
        }
        
        response = client.post('/api/webhook/whatsapp',
                              data=json.dumps(webhook_payload),
                              content_type='application/json')
        
        assert response.status_code == 200
        assert response.json['status'] == 'processed'
        assert response.json['success'] == 1
        
        # Verify message updated
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT delivered_at, read_at, failed_at 
                FROM task_messages 
                WHERE whatsapp_message_id = ?
            """, (whatsapp_msg_id,))
            row = cursor.fetchone()
            
            assert row['delivered_at'] is not None
            assert row['read_at'] is None
            assert row['failed_at'] is None
    
    def test_webhook_read_status_update(self, client, sample_project, sample_employee, mock_kapso):
        """Test read status webhook updates message."""
        task_id, whatsapp_msg_id, _ = self._create_task_with_message(
            client, sample_project, sample_employee
        )
        
        # Send read status webhook
        webhook_payload = {
            'statuses': [{
                'id': whatsapp_msg_id,
                'status': 'read',
                'timestamp': '1706500100',
                'recipient_id': '918005800336'
            }]
        }
        
        response = client.post('/api/webhook/whatsapp',
                              data=json.dumps(webhook_payload),
                              content_type='application/json')
        
        assert response.status_code == 200
        assert response.json['status'] == 'processed'
        
        # Verify message updated
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT read_at, read_receipt_available, read_inferred 
                FROM task_messages 
                WHERE whatsapp_message_id = ?
            """, (whatsapp_msg_id,))
            row = cursor.fetchone()
            
            assert row['read_at'] is not None
            assert row['read_receipt_available'] == 1
            assert row['read_inferred'] == 0
    
    def test_webhook_failed_status_update(self, client, sample_project, sample_employee, mock_kapso):
        """Test failed status webhook updates message with error."""
        task_id, whatsapp_msg_id, _ = self._create_task_with_message(
            client, sample_project, sample_employee
        )
        
        # Send failed status webhook
        webhook_payload = {
            'statuses': [{
                'id': whatsapp_msg_id,
                'status': 'failed',
                'timestamp': '1706500200',
                'recipient_id': '918005800336',
                'errors': [{
                    'code': 131026,
                    'title': 'Message Undeliverable',
                    'message': 'Phone number not registered on WhatsApp'
                }]
            }]
        }
        
        response = client.post('/api/webhook/whatsapp',
                              data=json.dumps(webhook_payload),
                              content_type='application/json')
        
        assert response.status_code == 200
        assert response.json['status'] == 'processed'
        
        # Verify message updated
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT failed_at, failure_reason 
                FROM task_messages 
                WHERE whatsapp_message_id = ?
            """, (whatsapp_msg_id,))
            row = cursor.fetchone()
            
            assert row['failed_at'] is not None
            assert '131026' in row['failure_reason']
            assert 'Message Undeliverable' in row['failure_reason']
    
    def test_read_inference_from_text_reply(self, client, sample_project, sample_employee, mock_kapso):
        """Test read status inferred when user replies with text."""
        task_id, whatsapp_msg_id, _ = self._create_task_with_message(
            client, sample_project, sample_employee
        )
        
        # Send text reply webhook
        webhook_payload = {
            'message': {
                'from': '918005800336',
                'type': 'text',
                'text': {
                    'body': 'I am working on this task'
                },
                'context': {
                    'id': whatsapp_msg_id
                }
            }
        }
        
        response = client.post('/api/webhook/whatsapp',
                              data=json.dumps(webhook_payload),
                              content_type='application/json')
        
        assert response.status_code == 200
        
        # Verify read status inferred
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT read_at, read_receipt_available, read_inferred 
                FROM task_messages 
                WHERE whatsapp_message_id = ?
            """, (whatsapp_msg_id,))
            row = cursor.fetchone()
            
            assert row['read_at'] is not None
            assert row['read_receipt_available'] == 0
            assert row['read_inferred'] == 1
    
    def test_read_inference_from_media_reply(self, client, sample_project, sample_employee, mock_kapso):
        """Test read status inferred when user replies with media."""
        task_id, whatsapp_msg_id, _ = self._create_task_with_message(
            client, sample_project, sample_employee
        )
        
        # Send media reply webhook (mocked file download)
        webhook_payload = {
            'message': {
                'from': '918005800336',
                'type': 'image',
                'image': {
                    'id': 'test_media_id',
                    'caption': 'Task progress photo'
                },
                'context': {
                    'id': whatsapp_msg_id
                },
                'kapso': {
                    'media_url': 'https://example.com/test.jpg',
                    'media_data': {
                        'filename': 'progress.jpg',
                        'content_type': 'image/jpeg'
                    }
                }
            }
        }
        
        # Mock file download
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = b'fake_image_data'
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            response = client.post('/api/webhook/whatsapp',
                                  data=json.dumps(webhook_payload),
                                  content_type='application/json')
        
        assert response.status_code == 200
        
        # Verify read status inferred
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT read_at, read_receipt_available, read_inferred 
                FROM task_messages 
                WHERE whatsapp_message_id = ?
            """, (whatsapp_msg_id,))
            row = cursor.fetchone()
            
            assert row['read_at'] is not None
            assert row['read_receipt_available'] == 0
            assert row['read_inferred'] == 1
    
    def test_duplicate_status_webhooks_handled(self, client, sample_project, sample_employee, mock_kapso):
        """Test duplicate status webhooks are ignored."""
        task_id, whatsapp_msg_id, _ = self._create_task_with_message(
            client, sample_project, sample_employee
        )
        
        # Send delivery status webhook
        webhook_payload = {
            'statuses': [{
                'id': whatsapp_msg_id,
                'status': 'delivered',
                'timestamp': '1706500000',
                'recipient_id': '918005800336'
            }]
        }
        
        # First delivery
        response1 = client.post('/api/webhook/whatsapp',
                               data=json.dumps(webhook_payload),
                               content_type='application/json')
        assert response1.status_code == 200
        assert response1.json['status'] == 'processed'
        assert response1.json['success'] == 1
        
        # Duplicate delivery (should be ignored)
        response2 = client.post('/api/webhook/whatsapp',
                               data=json.dumps(webhook_payload),
                               content_type='application/json')
        assert response2.status_code == 200
        assert response2.json['status'] == 'processed'
        # Should have 0 successes (all ignored)
        assert response2.json['success'] == 0
    
    def test_status_history_logged(self, client, sample_project, sample_employee, mock_kapso):
        """Test all status changes are logged to history."""
        task_id, whatsapp_msg_id, message_id = self._create_task_with_message(
            client, sample_project, sample_employee
        )
        
        # Send delivery webhook
        webhook_payload1 = {
            'statuses': [{
                'id': whatsapp_msg_id,
                'status': 'delivered',
                'timestamp': '1706500000',
                'recipient_id': '918005800336'
            }]
        }
        client.post('/api/webhook/whatsapp',
                   data=json.dumps(webhook_payload1),
                   content_type='application/json')
        
        # Send read webhook
        webhook_payload2 = {
            'statuses': [{
                'id': whatsapp_msg_id,
                'status': 'read',
                'timestamp': '1706500100',
                'recipient_id': '918005800336'
            }]
        }
        client.post('/api/webhook/whatsapp',
                   data=json.dumps(webhook_payload2),
                   content_type='application/json')
        
        # Verify history entries
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT old_status, new_status, timestamp 
                FROM message_status_history 
                WHERE message_id = ?
                ORDER BY timestamp ASC
            """, (message_id,))
            
            history = cursor.fetchall()
            assert len(history) == 2
            
            # First entry: sent -> delivered
            assert history[0]['old_status'] == 'sent'
            assert history[0]['new_status'] == 'delivered'
            
            # Second entry: delivered -> read
            assert history[1]['old_status'] == 'delivered'
            assert history[1]['new_status'] == 'read'



class TestPhase2BackwardCompatibility:
    """Test suite for backward compatibility with Phase 1."""
    
    def test_existing_tasks_unaffected(self, client, sample_employee):
        """Verify existing tasks work with new schema."""
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create task using Phase 1 logic
            task_data = {
                'projectId': 1,
                'title': "Legacy Task",
                'description': "Testing backward compatibility",
                'assignedTo': sample_employee,
                'dueDate': '2026-02-01',
                'priority': 'medium',
                'status': 'assigned'
            }
            result = db.tasks.create_task(task_data)
            task = result['data']
            
            # Verify task created successfully
            cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task['task_id'],))
            assert cursor.fetchone() is not None
    
    def test_task_messages_without_new_columns(self, client, sample_employee):
        """Verify task messages can be inserted without new Phase 2 columns."""
        from datetime import datetime
        
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            task_data = {
                'projectId': 1,
                'title': "Legacy Message Test",
                'description': "Testing backward compatibility",
                'assignedTo': sample_employee,
                'dueDate': '2026-02-01',
                'priority': 'medium',
                'status': 'assigned'
            }
            result = db.tasks.create_task(task_data)
            task = result['data']
            
            # Insert message using only Phase 1 columns
            msg_id = get_unique_msg_id()
            cursor.execute("""
                INSERT INTO task_messages 
                (task_id, whatsapp_message_id, employee_phone, message_type)
                VALUES (?, ?, ?, ?)
            """, (task['task_id'], msg_id, '+919876543210', 'eod_check'))
            conn.commit()
            
            # Verify Phase 2 columns default properly
            message_id = cursor.lastrowid
            cursor.execute("""
                SELECT delivered_at, read_at, failed_at, read_inferred 
                FROM task_messages WHERE id = ?
            """, (message_id,))
            
            row = cursor.fetchone()
            assert row[0] is None  # delivered_at defaults to NULL
            assert row[1] is None  # read_at defaults to NULL
            assert row[2] is None  # failed_at defaults to NULL
            assert row[3] == 0  # read_inferred defaults to 0
    
    def test_task_activities_without_mention_columns(self, client, sample_employee):
        """Verify activities can be created without mention columns."""
        from datetime import datetime
        
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            task_data = {
                'projectId': 1,
                'title': "Legacy Activity Test",
                'description': "Testing backward compatibility",
                'assignedTo': sample_employee,
                'dueDate': '2026-02-01',
                'priority': 'medium',
                'status': 'assigned'
            }
            result = db.tasks.create_task(task_data)
            task = result['data']
            
            # Insert activity using Phase 1 columns only
            cursor.execute("""
                INSERT INTO task_activities
                (task_id, author_type, author_id, activity_type, source, message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (task['task_id'], 'employee', sample_employee, 'comment', 'whatsapp_reply', 
                  'Test comment'))
            conn.commit()
            
            # Verify Phase 2 columns default properly
            activity_id = cursor.lastrowid
            cursor.execute("""
                SELECT mention_notification_sent, mention_notification_message_id 
                FROM task_activities WHERE id = ?
            """, (activity_id,))
            
            row = cursor.fetchone()
            assert row[0] == 0  # mention_notification_sent defaults to 0
            assert row[1] is None  # mention_notification_message_id defaults to NULL


# ============================================================================
# WhatsApp Integration Standalone Tests
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

