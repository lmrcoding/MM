# tests/conftest.py

import sys
import os
import pytest

# --- Keep your existing path setup ---
# Add the project root directory to sys.path so tests can import app modules.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- New: automatically run tests in "test" mode ---
@pytest.fixture(autouse=True)
def mm_test_env():
    """
    Force Metro Match into test mode for every test run.
    Why:
      - Enables safe middleware bypass when header 'X-Bypass-Loop: true' is present.
      - Prevents bypass from working in dev/staging/prod environments.
    """
    original = os.environ.get("MM_ENV")
    os.environ["MM_ENV"] = "test"
    try:
        yield
    finally:
        # Restore whatever was set before, to avoid leaking test state.
        if original is None:
            os.environ.pop("MM_ENV", None)
        else:
            os.environ["MM_ENV"] = original
