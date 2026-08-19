"""
fix_placeholder_files.py

Cleans up literal '\\n' sequences in placeholder module files.
"""

from pathlib import Path

def fix_placeholders():
    count = 0
    for p in Path("src").rglob("*.py"):
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            if "\\n" in text:
                clean_text = text.replace("\\n", "\n")
                p.write_text(clean_text, encoding="utf-8")
                count += 1
    print(f"Cleaned {count} placeholder files.")

if __name__ == "__main__":
    fix_placeholders()
