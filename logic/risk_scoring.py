SESSION_RISK_SCORES = {}

def update_risk_score(session_id: str, event_type: str) -> int:
    score = SESSION_RISK_SCORES.get(session_id, 0)

    if event_type == "tool_blocked":
        score += 3
    elif event_type == "loop_detected":
        score += 5
    elif event_type == "suspicious_input":
        score += 2
    elif event_type == "normal_use":
        score = max(score - 1, 0)

    SESSION_RISK_SCORES[session_id] = score
    return score
