# tests/test_logger_sanitization.py

import os
import time
from utils.logger import logger

LOG_FILE_PATH = "logs/agent_calls.log"

def clear_log_file():
    """Clears the log file before each test to avoid stale data."""
    with open(LOG_FILE_PATH, "w") as file:
        file.write("")

def read_latest_log_line() -> str:
    """Reads the most recent line from the log file."""
    with open(LOG_FILE_PATH, "r") as log_file:
        lines = log_file.readlines()
        return lines[-1] if lines else ""

def test_email_masking_in_logs():
    clear_log_file()

    test_message = "User signed up with email john.doe@example.com"
    logger.info(test_message)
    time.sleep(0.2)  # Allow logger to flush

    last_line = read_latest_log_line()
    print("Email Log Line:", last_line)
    assert "***@example.com" in last_line
    assert "john.doe@" not in last_line

def test_phone_masking_in_logs():
    clear_log_file()

    test_message = "User's phone number is 123-456-7890"
    logger.info(test_message)
    time.sleep(0.2)

    last_line = read_latest_log_line()
    print("Phone Log Line:", last_line)
    assert "***REDACTED PHONE***" in last_line
    assert "123-456-7890" not in last_line

def test_combined_email_and_phone():
    clear_log_file()

    test_message = "Contact: sarah@mail.com, phone: (555) 321-9876"
    logger.info(test_message)
    time.sleep(0.2)

    last_line = read_latest_log_line()
    print("Combined Log Line:", last_line)
    assert "***@mail.com" in last_line
    assert "***REDACTED PHONE***" in last_line
    assert "sarah@" not in last_line
    assert "321-9876" not in last_line
