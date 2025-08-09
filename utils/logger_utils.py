# utils/logger_utils.py

import re

def mask_email(text: str) -> str:
    """
    Replaces the user part of emails with ***.
    Example: john.doe@example.com -> ***@example.com
    """
    email_pattern = r'([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
    return re.sub(email_pattern, r'***@\2', text)

def mask_phone(text: str) -> str:
    """
    Masks phone numbers in a given text.
    Supports common formats (xxx-xxx-xxxx, (xxx) xxx-xxxx, etc.)
    """
    phone_pattern = r'(\+?\d{1,2}[\s\-]?)?(\(?\d{3}\)?[\s\-]?)?\d{3}[\s\-]?\d{4}'
    return re.sub(phone_pattern, '***REDACTED PHONE***', text)

def sanitize_log_text(text: str) -> str:
    """
    Applies all masking rules to the input text.
    Call this before sending anything to the logger.
    """
    text = mask_email(text)
    text = mask_phone(text)
    return text
