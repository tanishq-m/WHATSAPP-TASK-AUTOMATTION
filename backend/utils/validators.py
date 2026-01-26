"""
Validation utility functions.
"""

def validate_phone(phone):
    """
    Validate phone number format.
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
        
    Valid format: starts with + followed by country code and number
    Example: +919876543210, +14155552345
    """
    if not phone or not isinstance(phone, str):
        return False
    
    phone = phone.strip()
    
    # Must start with + and be at least 10 characters
    if not phone.startswith('+') or len(phone) < 10:
        return False
    
    # Remove + and check if remaining characters are digits
    digits_only = phone[1:]
    if not digits_only.isdigit():
        return False
    
    return True