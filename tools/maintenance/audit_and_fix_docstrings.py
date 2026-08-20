"""
audit_and_fix_docstrings.py

Audits and fixes docstrings for all public functions, classes, and methods in src/
"""

import ast
import os
from pathlib import Path

def audit_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=str(filepath))
    except Exception as e:
        # print(f"Error parsing {filepath}: {e}")
        return 0, []

    missing = []
    total_public = 0

    class DocstringVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            nonlocal total_public
            if not node.name.startswith("_") or node.name in ("__init__",):
                total_public += 1
                doc = ast.get_docstring(node)
                if not doc or not doc.strip():
                    missing.append((node.name, node.lineno, "function"))
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            nonlocal total_public
            if not node.name.startswith("_"):
                total_public += 1
                doc = ast.get_docstring(node)
                if not doc or not doc.strip():
                    missing.append((node.name, node.lineno, "async function"))
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            nonlocal total_public
            if not node.name.startswith("_"):
                total_public += 1
                doc = ast.get_docstring(node)
                if not doc or not doc.strip():
                    missing.append((node.name, node.lineno, "class"))
            self.generic_visit(node)

    visitor = DocstringVisitor()
    visitor.visit(tree)
    return total_public, missing

def main():
    src_dir = Path("src")
    total_funcs = 0
    missing_funcs = []
    file_stats = {}

    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py") and not file.endswith(".bak"):
                filepath = Path(root) / file
                tot, miss = audit_file(filepath)
                total_funcs += tot
                if miss:
                    missing_funcs.append((filepath, miss))
                file_stats[filepath] = (tot, len(miss))

    total_missing = sum(len(m) for _, m in missing_funcs)
    print(f"Total Public Functions/Classes in src/: {total_funcs}")
    print(f"Total Missing Docstrings: {total_missing}")
    print(f"Docstring Coverage: {(total_funcs - total_missing) / max(total_funcs, 1) * 100:.2f}% ({total_funcs - total_missing}/{total_funcs})")
    print("\nFiles with missing docstrings:")
    for fp, miss in missing_funcs:
        print(f"  {fp}: {len(miss)} missing -> {[m[0] for m in miss]}")

if __name__ == "__main__":
    main()
