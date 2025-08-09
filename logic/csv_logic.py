import csv
from typing import Dict, Any

CSV_FILE = "data/agent_rules.csv"

def match_from_csv(user_input: Dict[str, Any]) -> Dict[str, Any]:
    try:
        with open(CSV_FILE, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                match = True
                for key in user_input:
                    if row.get(key) and str(user_input[key]).lower() != str(row[key]).lower():
                        match = False
                        break

                if match:
                    return {
                        "match_found": True,
                        "matched_tool": row.get("tool"),
                        "response": row.get("response"),
                        "row": row
                    }

        return {"match_found": False}

    except Exception as e:
        return {"match_found": False, "error": str(e)}
