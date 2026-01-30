"""
Mention Service
Handles @mention parsing and WhatsApp notifications for mentions.
"""

import re
import db.tasks
import db.employees
import db.activities
import services.kapso_service as kapso_service


def parse_mentions(text):
    """
    Parse @mentions from text.
    
    Supports formats:
    - @JohnDoe
    - @John Doe
    - @John.Doe
    - @john-doe
    
    Args:
        text (str): Comment text
        
    Returns:
        list: List of mentioned names (without @)
    """
    if not text:
        return []
    
    # Pattern: @ followed by word characters, spaces, dots, or hyphens
    # Capture until we hit a word boundary followed by lowercase word (like "please", "can", etc.)
    # or punctuation, or end of string
    pattern = r'@([\w][\w\s\.\-]*?)(?=\s+(?:please|can|should|could|will|would|check|help|review|see|look|and|or|but|the|this|that|is|are|was|were|in|on|at|to|for|with)[^\w]|\s*[,;:!?\.]|\s*@|\s*$)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    # If no matches with common words, try simpler pattern (just punctuation)
    if not matches:
        pattern = r'@([\w][\w\s\.\-]*?)(?=\s*[,;:!?\.]|\s*@|\s*$)'
        matches = re.findall(pattern, text)
    
    # Clean up: strip whitespace and return unique mentions
    mentions = [m.strip() for m in matches if m.strip()]
    return list(set(mentions))


def find_employee_by_mention(mention_name):
    """
    Find employee by mentioned name.
    Tries exact match first, then case-insensitive partial match.
    
    Args:
        mention_name (str): Mentioned name (without @)
        
    Returns:
        dict: Employee data or None if not found
    """
    # Get all employees
    result = db.employees.get_all_employees()
    if not result['success']:
        return None
    
    employees = result['data']
    mention_lower = mention_name.lower()
    
    # Try exact match first (case-insensitive)
    for emp in employees:
        if emp['name'].lower() == mention_lower:
            return emp
    
    # Try partial match (name contains mention or vice versa)
    for emp in employees:
        emp_name_lower = emp['name'].lower()
        if mention_lower in emp_name_lower or emp_name_lower in mention_lower:
            return emp
    
    return None


def process_mentions_in_comment(task_id, activity_id, comment_text, author_name):
    """
    Process all mentions in a comment and send WhatsApp notifications.
    
    Args:
        task_id (str): Task ID
        activity_id (int): Activity ID
        comment_text (str): Comment text with mentions
        author_name (str): Name of person who made the comment
        
    Returns:
        dict: Summary of mention processing
    """
    mentions = parse_mentions(comment_text)
    
    if not mentions:
        return {
            'success': True,
            'mentions_found': 0,
            'notifications_sent': 0
        }
    
    print(f"📢 Found {len(mentions)} mentions in comment")
    
    notifications_sent = 0
    notifications_failed = 0
    invalid_mentions = []
    
    for mention_name in mentions:
        print(f"🔍 Processing mention: @{mention_name}")
        
        # Find employee
        employee = find_employee_by_mention(mention_name)
        
        if not employee:
            print(f"⚠️ No employee found for mention: @{mention_name}")
            invalid_mentions.append(mention_name)
            continue
        
        print(f"✅ Found employee: {employee['name']} ({employee['phone']})")
        
        # Send WhatsApp notification
        try:
            notification_result = send_mention_notification(
                task_id=task_id,
                activity_id=activity_id,
                employee=employee,
                comment_text=comment_text,
                author_name=author_name
            )
            
            if notification_result['success']:
                notifications_sent += 1
            else:
                notifications_failed += 1
                
        except Exception as e:
            print(f"❌ Failed to send mention notification: {e}")
            notifications_failed += 1
    
    return {
        'success': True,
        'mentions_found': len(mentions),
        'notifications_sent': notifications_sent,
        'notifications_failed': notifications_failed,
        'invalid_mentions': invalid_mentions
    }


def send_mention_notification(task_id, activity_id, employee, comment_text, author_name):
    """
    Send WhatsApp notification to mentioned employee.
    
    Args:
        task_id (str): Task ID
        activity_id (int): Activity ID
        employee (dict): Employee data
        comment_text (str): Comment text
        author_name (str): Name of person who made the comment
        
    Returns:
        dict: Result with success status and message ID
    """
    # Get task details
    task_result = db.tasks.get_task_by_id(task_id)
    if not task_result['success']:
        return {'success': False, 'error': 'Task not found'}
    
    task = task_result['data']
    
    # Format notification message
    message = format_mention_notification(
        task_title=task['title'],
        task_id=task_id,
        author_name=author_name,
        comment_text=comment_text,
        employee_name=employee['name']
    )
    
    # Send WhatsApp message
    clean_phone = employee['phone'].replace('+', '')
    result = kapso_service.send_text_message(clean_phone, message)
    
    if result.get('success'):
        # Get WhatsApp message ID
        whatsapp_message_id = None
        if result.get('data') and result['data'].get('messages'):
            whatsapp_message_id = result['data']['messages'][0].get('id')
        
        # Update activity with notification info
        db.activities.update_activity_mention_notification(
            activity_id=activity_id,
            mentioned_employee_id=employee['id'],
            whatsapp_message_id=whatsapp_message_id
        )
        
        # IMPORTANT: Track this message ID for reply threading
        # This allows employee replies to ANY task-related message to be captured
        if whatsapp_message_id:
            db.activities.create_task_message(
                task_id,
                whatsapp_message_id,
                employee['phone']
            )
            print(f"✅ Tracked mention notification message for reply threading")
        
        print(f"✅ Mention notification sent to {employee['name']}")
        
        return {
            'success': True,
            'whatsapp_message_id': whatsapp_message_id
        }
    else:
        print(f"❌ Failed to send mention notification: {result.get('error')}")
        return {
            'success': False,
            'error': result.get('error')
        }


def format_mention_notification(task_title, task_id, author_name, comment_text, employee_name):
    """
    Format WhatsApp notification message for mention.
    
    Args:
        task_title (str): Task title
        task_id (str): Task ID
        author_name (str): Name of person who made the comment
        comment_text (str): Comment text
        employee_name (str): Name of mentioned employee
        
    Returns:
        str: Formatted WhatsApp message
    """
    # Truncate comment if too long
    max_comment_length = 200
    display_comment = comment_text
    if len(comment_text) > max_comment_length:
        display_comment = comment_text[:max_comment_length] + "..."
    
    message = f"""👋 Hi {employee_name}!

*{author_name}* mentioned you in a comment on task:

📋 *{task_title}* (#{task_id})

💬 Comment:
"{display_comment}"

You can reply to this message to add your response."""
    
    return message
