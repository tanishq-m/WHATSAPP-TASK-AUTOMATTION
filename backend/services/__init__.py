"""
Services package for WhatsApp Task Manager.
Contains external service integrations.
"""

from services.kapso_service import (
    send_text_message,
    send_task_assignment,
    send_task_with_status_request,
)

__all__ = [
    'send_text_message',
    'send_task_assignment', 
    'send_task_with_status_request',
]
