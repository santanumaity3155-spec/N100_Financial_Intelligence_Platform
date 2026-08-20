"""
fix_only_placeholders.py

Safely fixes placeholder files that literally contain standard placeholder string with escaped \\n.
"""

from pathlib import Path

def fix_only():
    count = 0
    for p in Path("src").rglob("*.py"):
        if p.is_file():
            text = p.read_text(encoding="utf-8-sig", errors="replace")
            if text.strip() == '"""Placeholder module."""\\n' or text.strip() == '"""Placeholder module."""\\\\n':
                p.write_text('"""Placeholder module."""\n', encoding="utf-8")
                count += 1
    print(f"Fixed {count} exact placeholder files.")

if __name__ == "__main__":
    fix_only()
