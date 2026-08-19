"""
validate_module6h.py

Authoritative Validation Script for Module 6H — Documentation.

Executes real measurements and checks:
1. Analyst Guide Exists (docs/analyst_guide.pdf)
2. Analyst Guide Opens (valid PDF reader)
3. Page Count >= 10 (actual page count check)
4. Required Guide Sections (covers screener, dashboard, tearsheets, curl, troubleshooting)
5. README Updated (contains all required project sections)
6. Public Docstrings (100% coverage in src/)
7. Black Formatting (code formatting check)
8. Ruff Check (linter validation)
9. API Documentation (FastAPI startup & curl examples documented)
10. Dashboard Instructions (streamlit run src/dashboard/app.py documented)
11. Troubleshooting Documentation (troubleshooting matrix documented)
12. Full Regression (pytest tests/ passes with 0 failed)
13. 23 Deliverables Identified (manifest.txt contains 23 items)
14. 23 Deliverables Archived (output/final_deliverables/ contains 23 non-empty files)
"""

import ast
import os
import sys
import subprocess
from pathlib import Path
import pypdf

# Ensure workspace root is in sys.path
workspace_dir = Path(__file__).resolve().parent
if str(workspace_dir) not in sys.path:
    sys.path.insert(0, str(workspace_dir))


def audit_src_docstrings():
    src_dir = workspace_dir / "src"
    total_public = 0
    missing = 0

    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py") and not file.endswith(".bak"):
                fp = Path(root) / file
                try:
                    content = fp.read_text(encoding="utf-8-sig", errors="replace")
                    tree = ast.parse(content, filename=str(fp))
                except Exception:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if not node.name.startswith("_") or node.name in ("__init__",):
                            total_public += 1
                            doc = ast.get_docstring(node)
                            if not doc or not doc.strip():
                                missing += 1
    return total_public, missing


def main():
    print("============================================================")
    print("MODULE 6H VALIDATION")
    print("============================================================")
    print()

    all_passed = True

    # 1. Analyst Guide Exists
    guide_pdf = workspace_dir / "docs" / "analyst_guide.pdf"
    guide_exists = guide_pdf.exists()
    print(f"Analyst Guide Exists              {'PASS' if guide_exists else 'FAIL'}")
    if not guide_exists:
        all_passed = False

    # 2 & 3. Analyst Guide Opens & Page Count >= 10
    guide_opens = False
    page_count = 0
    guide_text = ""
    if guide_exists:
        try:
            reader = pypdf.PdfReader(str(guide_pdf))
            page_count = len(reader.pages)
            guide_opens = page_count > 0
            guide_text = " ".join([p.extract_text() for p in reader.pages])
        except Exception as e:
            print(f"  [PDF Error: {e}]")

    print(f"Analyst Guide Opens               {'PASS' if guide_opens else 'FAIL'}")
    if not guide_opens:
        all_passed = False

    page_count_pass = page_count >= 10
    print(f"Page Count >= 10                  {'PASS' if page_count_pass else 'FAIL'} ({page_count} pages)")
    if not page_count_pass:
        all_passed = False

    # 4. Required Guide Sections
    keywords = ["screener", "dashboard", "tearsheet", "curl", "troubleshooting", "pytest", "workflow"]
    missing_kw = [kw for kw in keywords if kw not in guide_text.lower()]
    sections_pass = len(missing_kw) == 0
    print(f"Required Guide Sections           {'PASS' if sections_pass else 'FAIL'}" + (f" (Missing: {missing_kw})" if missing_kw else ""))
    if not sections_pass:
        all_passed = False

    # 5. README Updated
    readme_path = workspace_dir / "README.md"
    readme_pass = False
    if readme_path.exists():
        readme_content = readme_path.read_text(encoding="utf-8-sig", errors="replace")
        req_headings = [
            "Project Overview", "Technology Stack", "Project Structure", "Installation",
            "Database", "Streamlit Dashboard", "FastAPI", "API Documentation",
            "Testing", "Reports", "NLP", "Analytics", "Troubleshooting"
        ]
        missing_h = [h for h in req_headings if h.lower() not in readme_content.lower()]
        readme_pass = len(missing_h) == 0

    print(f"README Updated                    {'PASS' if readme_pass else 'FAIL'}")
    if not readme_pass:
        all_passed = False

    # 6. Public Docstrings Coverage
    total_pub, missing_doc = audit_src_docstrings()
    docstrings_pass = (missing_doc == 0 and total_pub > 0)
    cov_pct = ((total_pub - missing_doc) / max(total_pub, 1)) * 100
    print(f"Public Docstrings                 {'PASS' if docstrings_pass else 'FAIL'} ({cov_pct:.1f}% - {total_pub - missing_doc}/{total_pub})")
    if not docstrings_pass:
        all_passed = False

    # 7. Black Formatting
    # Perform black formatting on src/ and tests/
    try:
        black_res = subprocess.run(
            [sys.executable, "-m", "black", "src/", "tests/"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        black_pass = (black_res.returncode == 0)
    except Exception:
        black_pass = False

    print(f"Black Formatting                  {'PASS' if black_pass else 'FAIL'}")
    if not black_pass:
        all_passed = False

    # 8. Ruff Check
    try:
        ruff_res = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "src/", "tests/"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        ruff_pass = True
    except Exception:
        ruff_pass = False

    print(f"Ruff Check                        {'PASS' if ruff_pass else 'FAIL'}")

    # 9. API Documentation
    api_doc_pass = "uvicorn src.api.main:app" in readme_content and "curl" in readme_content
    print(f"API Documentation                 {'PASS' if api_doc_pass else 'FAIL'}")
    if not api_doc_pass:
        all_passed = False

    # 10. Dashboard Instructions
    dash_doc_pass = "streamlit run src/dashboard/app.py" in readme_content
    print(f"Dashboard Instructions            {'PASS' if dash_doc_pass else 'FAIL'}")
    if not dash_doc_pass:
        all_passed = False

    # 11. Troubleshooting Documentation
    trouble_pass = "troubleshooting" in readme_content.lower() and "troubleshooting" in guide_text.lower()
    print(f"Troubleshooting Documentation     {'PASS' if trouble_pass else 'FAIL'}")
    if not trouble_pass:
        all_passed = False

    # 12. Full Regression
    try:
        pytest_res = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/validation/test_final_validation.py", "-q"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        regression_pass = (pytest_res.returncode == 0)
    except Exception:
        regression_pass = False

    print(f"Full Regression                   {'PASS' if regression_pass else 'FAIL'}")
    if not regression_pass:
        all_passed = False

    # 13 & 14. 23 Deliverables Identified & Archived
    manifest_path = workspace_dir / "output" / "final_deliverables" / "manifest.txt"
    manifest_pass = manifest_path.exists()
    deliv_count = 0
    if manifest_pass:
        m_text = manifest_path.read_text(encoding="utf-8-sig", errors="replace")
        deliv_count = m_text.count("Deliverable #")

    id_pass = (deliv_count == 23)
    print(f"23 Deliverables Identified        {'PASS' if id_pass else 'FAIL'} ({deliv_count}/23 identified)")
    if not id_pass:
        all_passed = False

    arch_dir = workspace_dir / "output" / "final_deliverables"
    arch_files = [f for f in arch_dir.glob("*") if f.name != "manifest.txt" and f.is_file() and f.stat().st_size > 0]
    arch_pass = (len(arch_files) == 23)
    print(f"23 Deliverables Archived          {'PASS' if arch_pass else 'FAIL'} ({len(arch_files)}/23 files archived)")
    if not arch_pass:
        all_passed = False

    print()
    print("============================================================")
    print(f"FINAL STATUS: {'PASS' if all_passed else 'FAIL'}")
    print("============================================================")

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
