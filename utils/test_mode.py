# utils/test_mode.py

import os

def is_test_mode() -> bool:
    """
    Return True when the code is running under pytest.
    Why this works:
      - PYTEST_CURRENT_TEST is set by pytest during test collection/execution.
      - MM_TEST_MODE=1 lets you force test mode if you ever need to.
    """
    return "PYTEST_CURRENT_TEST" in os.environ or os.getenv("MM_TEST_MODE") == "1"
