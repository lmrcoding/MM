from collections import defaultdict
import time

TOOL_QUOTA = {
    "InventoryCheck": 5,
    "VendorMatch": 3,
    "RefillRequest": 2
}

user_tool_usage = defaultdict(list)

def track_tool_usage(user_id: str, tool_name: str) -> bool:
    now = time.time()
    window = 3600  # 1 hour

    usage_log = user_tool_usage[(user_id, tool_name)]
    usage_log = [t for t in usage_log if now - t < window]

    if len(usage_log) >= TOOL_QUOTA.get(tool_name, 1):
        return False  # Over quota

    usage_log.append(now)
    user_tool_usage[(user_id, tool_name)] = usage_log
    return True
