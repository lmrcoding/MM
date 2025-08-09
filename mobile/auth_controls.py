import time

SESSION_TIMEOUT = 900  # 15 minutes

session_last_active = {}

def update_session_activity(session_id: str):
    session_last_active[session_id] = time.time()

def is_reauth_required(session_id: str) -> bool:
    last_active = session_last_active.get(session_id, 0)
    return (time.time() - last_active) > SESSION_TIMEOUT
