import re

EMAIL_PATTERN = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
PHONE_PATTERN = r"\+?\d[\d\-\s]{7,}\d"
SECRET_PATTERN = r"(token|apikey|password|secret)=\S+"

def redact_sensitive_data(text: str) -> str:
    text = re.sub(EMAIL_PATTERN, "[REDACTED_EMAIL]", text)
    text = re.sub(PHONE_PATTERN, "[REDACTED_PHONE]", text)
    text = re.sub(SECRET_PATTERN, "[REDACTED_SECRET]", text)
    return text
