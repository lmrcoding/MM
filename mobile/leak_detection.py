import re
from utils.dlp import redact_sensitive_data

def detect_leakage(output_text: str) -> bool:
    redacted = redact_sensitive_data(output_text)
    return redacted != output_text
