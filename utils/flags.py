import json

def load_kill_switches(path="config/kill_switches.json") -> dict:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {}

def is_feature_enabled(feature_name: str, switches: dict) -> bool:
    return not switches.get(feature_name, False)
