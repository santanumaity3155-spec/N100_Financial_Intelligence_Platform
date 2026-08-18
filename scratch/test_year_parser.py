import re
from pathlib import Path

def validate_year_param(val: str) -> int:
    """Validate year param and return extracted integer year."""
    if not val:
        return None
    val_str = str(val).strip()
    m_full = re.match(r'^(\d{4})-(0[1-9]|1[0-2])$', val_str)
    if m_full:
        return int(m_full.group(1))
    m_year = re.match(r'^\d{4}$', val_str)
    if m_year:
        return int(m_year.group(0))
    raise ValueError(f"Invalid year format: {val}")

def extract_year_from_period(period_str: str) -> int:
    """Extract integer year from database period string."""
    if not period_str:
        return 0
    p = str(period_str).strip()
    m = re.search(r'\b(19\d\d|20\d\d)\b', p)
    if m:
        return int(m.group(1))
    m2 = re.search(r'-(1\d|2\d)\b', p)
    if m2:
        return 2000 + int(m2.group(1))
    return 0

# Test cases for year extraction
test_periods = [
    ('Dec 2012', 2012),
    ('Mar 2024', 2024),
    ('2024', 2024),
    ('2024.5', 2024),
    ('Mar-13', 2013),
    ('Mar-24', 2024),
]

for p, expected in test_periods:
    actual = extract_year_from_period(p)
    assert actual == expected, f"Failed for {p}: got {actual}, expected {expected}"

print("All year extraction tests passed!")
