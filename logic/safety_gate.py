from utils.flags import load_kill_switches, is_feature_enabled
from agents.tool_registry import TOOL_METADATA

def is_tool_allowed(tool_name: str, user_tier: str = "basic") -> bool:
    switches = load_kill_switches()

    if not is_feature_enabled(tool_name, switches):
        return False

    tool_info = TOOL_METADATA.get(tool_name, {})
    allowed_tiers = tool_info.get("allowed_tiers", ["basic"])

    return user_tier in allowed_tiers
