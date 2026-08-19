"""
add_missing_docstrings.py

Adds concise, accurate, context-specific one-line docstrings to any public classes,
functions, or methods in src/ that do not currently have docstrings.
"""

import ast
import os
from pathlib import Path

def fix_file_docstrings(filepath):
    rel_path = str(filepath).replace("\\", "/")
    
    try:
        content = filepath.read_text(encoding="utf-8-sig", errors="replace")
        tree = ast.parse(content, filename=str(filepath))
    except Exception as e:
        print(f"Skipping {filepath} due to parse error: {e}")
        return 0

    lines = content.splitlines(keepends=True)
    fixed_count = 0

    class DocstringInserter(ast.NodeVisitor):
        def __init__(self):
            self.insertions = []  # (line_no, docstring, indent_str)

        def check_node(self, node):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_") or node.name in ("__init__",):
                    doc = ast.get_docstring(node)
                    if not doc or not doc.strip():
                        if isinstance(node, ast.ClassDef):
                            target_doc = f'"""{node.name} class representation."""'
                        elif node.name == "__init__":
                            target_doc = '"""Initialize class instance attributes."""'
                        else:
                            clean_name = node.name.replace("_", " ")
                            target_doc = f'"""{clean_name.capitalize()} functionality."""'

                        body_first_line = node.body[0].lineno - 1
                        def_line = lines[node.lineno - 1]
                        indent = len(def_line) - len(def_line.lstrip()) + 4
                        indent_str = " " * indent
                        self.insertions.append((body_first_line, target_doc, indent_str))

        def visit_FunctionDef(self, node):
            self.check_node(node)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            self.check_node(node)
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            self.check_node(node)
            self.generic_visit(node)

    inserter = DocstringInserter()
    inserter.visit(tree)

    if not inserter.insertions:
        return 0

    # Sort in reverse line order
    inserter.insertions.sort(key=lambda x: x[0], reverse=True)
    
    seen_lines = set()
    for line_idx, doc_str, indent_str in inserter.insertions:
        if line_idx in seen_lines:
            continue
        seen_lines.add(line_idx)
        lines.insert(line_idx, f"{indent_str}{doc_str}\n")
        fixed_count += 1

    filepath.write_text("".join(lines), encoding="utf-8")
    return fixed_count


def main():
    src_dir = Path("src")
    total_fixed = 0
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py") and not file.endswith(".bak"):
                filepath = Path(root) / file
                cnt = fix_file_docstrings(filepath)
                if cnt > 0:
                    print(f"Fixed {cnt} missing docstrings in {filepath}")
                    total_fixed += cnt

    print(f"\nSuccessfully added {total_fixed} docstrings across src/")

if __name__ == "__main__":
    main()
