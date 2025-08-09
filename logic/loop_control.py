MAX_AGENT_HOPS = 5

def is_loop_detected(hop_count: int) -> bool:
    return hop_count > MAX_AGENT_HOPS
