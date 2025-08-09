from logic.csv_logic import match_from_csv
from logic.fallback_logic import fallback_response
from utils.logger import logger
from typing import Dict, Any

def agent_brain(user_input: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Received input: {user_input}")

    try:
        # ✅ Step 1: Input validation
        if "name" not in user_input or "query" not in user_input:
            logger.warning("Missing required input fields.")
            return {
                "status": "fallback",
                "details": {
                    "message": "Missing required input field(s).",
                    "input_echo": user_input
                }
            }

        # ✅ Step 2: CSV-based rule matching
        result = match_from_csv(user_input)

        if result.get("match_found"):
            logger.info("Match found via CSV logic.")
            return {"status": "matched", "details": result}

        # ✅ Step 3: Fallback if no match
        logger.warning("No match found. Using fallback.")
        return {"status": "fallback", "details": fallback_response(user_input)}

    except Exception as e:
        logger.error(f"Agent logic error: {str(e)}")
        return {"status": "error", "message": "Internal agent failure."}
