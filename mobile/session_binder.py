BOUND_SESSIONS = {}

def bind_session_to_device(session_id: str, device_fingerprint: str):
    BOUND_SESSIONS[session_id] = device_fingerprint

def is_session_valid(session_id: str, current_fingerprint: str) -> bool:
    expected = BOUND_SESSIONS.get(session_id)
    return expected == current_fingerprint
