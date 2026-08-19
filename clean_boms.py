"""
clean_boms.py

Safely removes UTF-8 BOM byte-order-mark from python files in src/ and tests/
while preserving original line endings.
"""

from pathlib import Path

def clean_boms():
    count = 0
    for folder in [Path("src"), Path("tests")]:
        for p in folder.rglob("*.py"):
            if p.is_file():
                try:
                    raw = p.read_bytes()
                    if raw.startswith(b"\xef\xbb\xbf"):
                        text = raw[3:].decode("utf-8")
                        p.write_text(text, encoding="utf-8", newline="")
                        count += 1
                except Exception as e:
                    print(f"Error processing {p}: {e}")
    print(f"Stripped UTF-8 BOM from {count} Python files.")

if __name__ == "__main__":
    clean_boms()
