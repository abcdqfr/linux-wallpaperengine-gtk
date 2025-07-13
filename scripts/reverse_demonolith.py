#!/usr/bin/env python3
"""Reverse demonolith: extract monolith into src/ structure."""

import ast
from pathlib import Path
from typing import Dict, List, Tuple


def extract_classes_and_functions(content: str) -> Dict[str, Tuple[int, int, str]]:
    """Extract classes and functions with their line ranges."""
    tree = ast.parse(content)
    items = {}

    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            start_line = node.lineno
            end_line = (
                node.end_lineno
                if hasattr(node, "end_lineno") and node.end_lineno is not None
                else start_line
            )

            # Get the source code for this item
            lines = content.split("\n")
            item_lines = lines[start_line - 1 : end_line]
            item_code = "\n".join(item_lines)

            items[node.name] = (start_line, end_line, item_code)

    return items


def extract_imports(content: str) -> List[str]:
    """Extract all import statements."""
    # TODO: Implement import extraction
    return []


def create_module_file(module_name: str, content: str, output_dir: Path) -> None:
    """Create a proper module file with imports and content."""
    # TODO: Implement module file creation
    print(f"Creating {module_name} module")


def reverse_demonolith(monolith_file: Path, output_dir: Path) -> None:
    """Reverse demonolith: extract monolith into src/ structure."""
    print(f"📦 Reverse demonolithing: {monolith_file} → {output_dir}")

    with open(monolith_file) as f:
        content = f.read()

    # Extract items
    items = extract_classes_and_functions(content)
    print(f"✅ Found {len(items)} classes/functions")


def main():
    """Main function."""
    monolith_file = Path("linux-wallpaperengine-gtk.py")
    output_dir = Path("src/wallpaperengine")

    if not monolith_file.exists():
        print(f"❌ Monolith file not found: {monolith_file}")
        return

    reverse_demonolith(monolith_file, output_dir)


if __name__ == "__main__":
    main()
