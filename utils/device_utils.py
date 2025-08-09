import hashlib

def generate_device_fingerprint(headers: dict) -> str:
    fingerprint_source = headers.get("user-agent", "") + headers.get("x-device-id", "")
    return hashlib.sha256(fingerprint_source.encode()).hexdigest()

def session_matches(fingerprint_1: str, fingerprint_2: str) -> bool:
    return fingerprint_1 == fingerprint_2
