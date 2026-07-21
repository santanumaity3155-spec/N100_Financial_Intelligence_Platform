"""
test_health_score.py

Integration test runner for Module 5 - Financial Health Score Engine.
Imports and runs the comprehensive test suite from tests/health_score/.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import pytest
    test_file = Path(__file__).resolve().parents[2] / "tests" / "health_score" / "test_health_score_engine.py"
    sys.exit(pytest.main(["-v", str(test_file)]))
