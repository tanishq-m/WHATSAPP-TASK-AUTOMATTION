"""
Kapso WhatsApp API Service.

This module handles all interactions with the Kapso WhatsApp API,
including sending text messages, interactive buttons, and task assignments.
"""

import requests
from datetime import datetime

# Hardcoded credentials (config.py wasn't reloading properly)
KAPSO_API_KEY = "7819cb622458c2ca2e3300008d391d85d39b962ee2b9996e8a562fa9408a5f81"
PHONE_NUMBER_ID = "597907523413541"
KAPSO_API_BASE = "https://api.kapso.ai/meta/whatsapp/v24.0"


def send_text_message(phone_number, message_text):
    """
    Send a text message via Kapso WhatsApp API.
    
    Args:
        phone_number (str): Phone number in format "919876543210" (without + sign)
        message_text (str): Message content to send
        
    Returns:
        dict: Response from Kapso API with 'success' and 'data' or 'error'
    """
    try:
        # Construct API endpoint
        url = f"{KAPSO_API_BASE}/{PHONE_NUMBER_ID}/messages"
        
        # Set headers
        headers = {
            "X-API-Key": KAPSO_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Prepare request body
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,  # Phone number without + sign
            "type": "text",
            "text": {
                "body": message_text
            }
        }
        
        print(f"📱 Sending WhatsApp message to {phone_number}...")
        print(f"🔗 URL: {url}")
        print(f"📝 Message: {message_text[:50]}..." if len(message_text) > 50 else f"📝 Message: {message_text}")
        print(f"📦 Payload: {payload}")
        
        # Make API request
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Body: {response.text}")
        
        # Check if request was successful
        if response.status_code == 200 or response.status_code == 201:
            response_data = response.json()
            print(f"✅ WhatsApp message sent successfully to {phone_number}")
            
            # Extract message ID from response for reply threading
            message_id = None
            if "messages" in response_data and len(response_data["messages"]) > 0:
                message_id = response_data["messages"][0].get("id")
            
            return {
                "success": True,
                "data": response_data,
                "message_id": message_id
            }
        else:
            error_msg = response.text
            print(f"❌ Kapso API Error: {response.status_code} - {error_msg}")
            return {
                "success": False,
                "error": f"Kapso API Error: {response.status_code} - {error_msg}"
            }
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error sending WhatsApp message: {str(e)}")
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        print(f"❌ Unexpected error sending WhatsApp message: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def send_task_assignment(employee_phone, task_data):
    """
    Send a formatted task assignment message to an employee.
    
    Args:
        employee_phone (str): Employee's phone number (without + sign)
        task_data (dict): Task information with keys:
            - task_id: Task ID (e.g., "task_001")
            - title: Task title
            - description: Task description
            - due_date: Due date (ISO format or readable)
            - priority: Priority level (high, medium, low)
            - employee_name: Employee's name (optional, for personalization)
            
    Returns:
        dict: Response from send_text_message()
    """
    try:
        # Extract task information
        task_id = task_data.get("task_id", "Unknown")
        title = task_data.get("title", "No title")
        description = task_data.get("description", "No description")
        due_date = task_data.get("due_date", "Not specified")
        priority = task_data.get("priority", "medium").upper()
        employee_name = task_data.get("employee_name", "Team Member")
        
        # Format priority with emoji
        priority_emoji = {
            "HIGH": "🔴",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        priority_display = f"{priority_emoji.get(priority, '⚪')} {priority}"
        
        # Construct message
        message = f"""Hi {employee_name},

You have been assigned a new task:

📋 *Task:* {title}
🆔 *ID:* {task_id}
📝 *Description:* {description}
📅 *Due Date:* {due_date}
⚡ *Priority:* {priority_display}

Please acknowledge receipt and start working on it. Good luck! 💪"""
        
        # Send message
        result = send_text_message(employee_phone, message)
        
        if result["success"]:
            print(f"✅ Task assignment sent to {employee_name} ({employee_phone})")
        else:
            print(f"❌ Failed to send task assignment to {employee_name}")
            
        return result
        
    except Exception as e:
        print(f"❌ Error formatting task assignment message: {str(e)}")
        return {
            "success": False,
            "error": f"Error formatting message: {str(e)}"
        }


def send_interactive_buttons(phone_number, body_text, buttons, header_text=None, footer_text=None):
    """
    Send an interactive button message via Kapso WhatsApp API.
    
    Args:
        phone_number (str): Phone number in format "919876543210" (without + sign)
        body_text (str): Main message content
        buttons (list): List of button dicts with 'id' and 'title' keys (max 3 buttons)
                       Example: [{"id": "completed", "title": "✅ Yes, Completed"}, 
                                {"id": "not_completed", "title": "❌ No, Not Yet"}]
        header_text (str, optional): Header text shown above body
        footer_text (str, optional): Footer text shown below buttons
        
    Returns:
        dict: Response from Kapso API with 'success' and 'data' or 'error'
    """
    try:
        # Validate buttons (max 3)
        if len(buttons) > 3:
            return {
                "success": False,
                "error": "Maximum 3 buttons allowed for interactive messages"
            }
        
        # Construct API endpoint
        url = f"{KAPSO_API_BASE}/{PHONE_NUMBER_ID}/messages"
        
        # Set headers
        headers = {
            "X-API-Key": KAPSO_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Build interactive message structure (Meta WhatsApp API format)
        interactive = {
            "type": "button",
            "body": {
                "text": body_text
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": btn["id"],
                            "title": btn["title"][:20]  # Max 20 chars for button title
                        }
                    }
                    for btn in buttons
                ]
            }
        }
        
        # Add optional header
        if header_text:
            interactive["header"] = {
                "type": "text",
                "text": header_text
            }
        
        # Add optional footer
        if footer_text:
            interactive["footer"] = {
                "text": footer_text
            }
        
        # Prepare request body
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "interactive",
            "interactive": interactive
        }
        
        print(f"📱 Sending interactive buttons to {phone_number}...")
        print(f"🔗 URL: {url}")
        print(f"📦 Buttons: {[btn['title'] for btn in buttons]}")
        
        # Make API request
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Body: {response.text}")
        
        # Check if request was successful
        if response.status_code in [200, 201]:
            response_data = response.json()
            print(f"✅ Interactive buttons sent successfully to {phone_number}")
            
            # Extract message ID from response for reply threading
            message_id = None
            if "messages" in response_data and len(response_data["messages"]) > 0:
                message_id = response_data["messages"][0].get("id")
            
            return {
                "success": True,
                "data": response_data,
                "message_id": message_id
            }
        else:
            error_msg = response.text
            print(f"❌ Kapso API Error: {response.status_code} - {error_msg}")
            return {
                "success": False,
                "error": f"Kapso API Error: {response.status_code} - {error_msg}"
            }
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error sending interactive buttons: {str(e)}")
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        print(f"❌ Unexpected error sending interactive buttons: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def send_task_with_status_request(employee_phone, task_data):
    """
    Send a task assignment with Yes/No buttons asking if task is completed.
    
    Args:
        employee_phone (str): Employee's phone number (without + sign)
        task_data (dict): Task information with keys:
            - task_id: Task ID (e.g., "task_001")
            - title: Task title
            - description: Task description  
            - due_date: Due date (ISO format or readable)
            - priority: Priority level (high, medium, low)
            - employee_name: Employee's name (optional)
            
    Returns:
        dict: Response from send_interactive_buttons()
    """
    try:
        # Extract task information
        task_id = task_data.get("task_id", "Unknown")
        title = task_data.get("title", "No title")
        description = task_data.get("description", "No description")
        due_date = task_data.get("due_date", "Not specified")
        priority = task_data.get("priority", "medium").upper()
        employee_name = task_data.get("employee_name", "Team Member")
        
        # Format priority with emoji
        priority_emoji = {
            "HIGH": "🔴",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        priority_display = f"{priority_emoji.get(priority, '⚪')} {priority}"
        
        # Construct body message
        body_text = f"""Hi {employee_name}! 👋

📋 *Task:* {title}
📝 *Details:* {description}
📅 *Due:* {due_date}
⚡ *Priority:* {priority_display}

Have you completed this task?"""
        
        # Define buttons with task_id encoded for tracking
        buttons = [
            {"id": f"completed_{task_id}", "title": "✅ Yes, Completed"},
            {"id": f"not_completed_{task_id}", "title": "❌ No, Not Yet"}
        ]
        
        # Optional header and footer
        header_text = "📋 Task Status Check"
        footer_text = f"Task ID: {task_id}"
        
        # Send interactive message
        result = send_interactive_buttons(
            phone_number=employee_phone,
            body_text=body_text,
            buttons=buttons,
            header_text=header_text,
            footer_text=footer_text
        )
        
        if result["success"]:
            print(f"✅ Task status request sent to {employee_name} ({employee_phone})")
        else:
            print(f"❌ Failed to send task status request to {employee_name}")
            
        return result
        
    except Exception as e:
        print(f"❌ Error formatting task status request: {str(e)}")
        return {
            "success": False,
            "error": f"Error formatting message: {str(e)}"
        }


# Example usage (for testing):
if __name__ == "__main__":
    # Test sending a simple message
    test_phone = "919876543210"  # Replace with your test number
    test_message = "Hello from WhatsApp Task Manager! 👋"
    
    print("Testing Kapso WhatsApp API...")
    result = send_text_message(test_phone, test_message)
    print(f"Result: {result}")
