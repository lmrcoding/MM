import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # 👈 This line is the fix

from logic.agent_brain import agent_brain

def test_agent_brain_basic_response():
    user_input = {
        "name": "Test User",
        "query": "I need help with inventory"
    }

    result = agent_brain(user_input)

    assert isinstance(result, dict), "Result should be a dictionary"
    assert "status" in result, "Result must contain a 'status' key"


def test_agent_brain_fallback_response():
    user_input = {
        "name": "Someone Not In CSV",
        "query": "This should trigger fallback"
    }

    result = agent_brain(user_input)

    assert isinstance(result, dict), "Result should be a dictionary"
    assert result.get("status") == "fallback", "Expected fallback status when no match is found"
    assert "details" in result, "Fallback result should contain 'details'"

def test_agent_brain_empty_query():
    user_input = {
        "name": "Test User",
        "query": ""
    }
    result = agent_brain(user_input)
    assert isinstance(result, dict)
    assert result["status"] in ["matched", "fallback"]


def test_agent_brain_missing_query_key():
    user_input = {
        "name": "Test User"
        # no 'query' key at all
    }
    result = agent_brain(user_input)
    assert isinstance(result, dict)
    assert result["status"] == "fallback"
    assert "details" in result


def test_agent_brain_unexpected_data_type():
    user_input = {
        "name": 12345,  # wrong type
        "query": True   # wrong type
    }
    result = agent_brain(user_input)
    assert isinstance(result, dict)
    assert result["status"] == "fallback"
