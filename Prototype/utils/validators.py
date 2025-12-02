"""
Input validation utilities for the application
"""
import re

def validate_email(email):
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False

    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Validate password strength
    Requirements:
    - At least 8 characters
    - Contains at least one letter
    - Contains at least one number
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"

    return True, "Password is valid"

def validate_username(username):
    """
    Validate username
    Requirements:
    - Between 3 and 50 characters
    - Only alphanumeric characters, underscores, and hyphens
    """
    if not username or not isinstance(username, str):
        return False, "Username is required"

    username = username.strip()

    if len(username) < 3:
        return False, "Username must be at least 3 characters long"

    if len(username) > 50:
        return False, "Username must be no more than 50 characters"

    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"

    return True, username

def sanitize_string(text, max_length=None):
    """
    Sanitize a string input by trimming whitespace
    """
    if not text or not isinstance(text, str):
        return ""

    text = text.strip()

    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text

def validate_module_number(module_number):
    """Validate module number is between 1 and 6"""
    if not isinstance(module_number, int):
        return False, "Module number must be an integer"

    if module_number < 1 or module_number > 6:
        return False, "Module number must be between 1 and 6"

    return True, module_number

def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present in data
    Returns tuple: (is_valid, missing_fields)
    """
    if not isinstance(data, dict):
        return False, []

    missing = [field for field in required_fields if not data.get(field)]

    return len(missing) == 0, missing
