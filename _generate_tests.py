"""Helper script to write test_pro_rules.py"""
content = """\"\"\"
test_pro_rules.py

Sprint 5 - Module 2B: Tests for PRO_01 - PRO_12.
\"\"\"

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nlp.pros_cons_generator import (
    CompanyContext,
    RuleResult,
    TYPE_PRO,
    validate_confidence,
)
from src.nlp.pro_rules import (
    PRO_01,
    PRO_02,
    PRO_03,
    PRO_04,
    PRO_05,
    PRO_06,
    PRO_07,
    PRO_08,
    PRO_09,
    PRO_10,
    PRO_11,
    PRO_12,
    get_pro_rule_instances,
)
from tests.nlp.test_pros_cons_generator import make_context

"""
