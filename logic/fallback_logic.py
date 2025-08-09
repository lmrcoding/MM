from typing import Dict, Any

def fallback_response(user_input: Dict[str, Any]) -> Dict[str, str]:
    return {
        "message": "No matching rule found. A specialist will review your request shortly.",
        "input_echo": str(user_input)
    }
