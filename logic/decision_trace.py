DECISION_LOGS = []

def log_decision_trace(user_input: dict, tool_used: str, decision_path: str):
    DECISION_LOGS.append({
        "input": user_input,
        "tool": tool_used,
        "path": decision_path
    })

def get_latest_trace() -> dict:
    return DECISION_LOGS[-1] if DECISION_LOGS else {}
