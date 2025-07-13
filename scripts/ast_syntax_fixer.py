#!/usr/bin/env python3
"""
AST-Powered Python Syntax Fixer with Dry-Run Capability
========================================================

Intelligently fixes Python syntax errors using AST analysis.
Designed to recover from autofix script disasters.
"""

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Union


class SyntaxFixer:
    """AST-powered syntax fixer with machine learning-like heuristics."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.fixes_applied = []
        self.errors_found = []

    def analyze_file(self, file_path: Path) -> Dict[str, Union[bool, List[str], str]]:
        """Analyze a Python file for syntax issues."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Try to parse with AST first
            try:
                ast.parse(content)
                return {
                    "valid": True,
                    "content": content,
                    "errors": [],
                    "fixes_needed": [],
                }
            except SyntaxError as e:
                return {
                    "valid": False,
                    "content": content,
                    "errors": [f"Line {e.lineno}: {e.msg}"],
                    "syntax_error": e,
                    "fixes_needed": self._analyze_syntax_error(content, e),
                }

        except Exception as e:
            return {
                "valid": False,
                "content": "",
                "errors": [f"File read error: {e}"],
                "fixes_needed": [],
            }

    def _analyze_syntax_error(self, content: str, error: SyntaxError) -> List[str]:
        """Analyze syntax error and suggest fixes."""
        fixes = []
        content.split("\n")
        error.lineno - 1 if error.lineno else 0

        # Common syntax error patterns and fixes
        if "unexpected indent" in error.msg.lower():
            fixes.append("Fix unexpected indentation")
        elif "unindent does not match" in error.msg.lower():
            fixes.append("Fix indentation level mismatch")
        elif "unterminated string" in error.msg.lower():
            fixes.append("Fix unterminated string literal")
        elif "unexpected eof" in error.msg.lower():
            fixes.append("Fix unexpected end of file")
        elif "invalid syntax" in error.msg.lower():
            fixes.append("Fix general syntax error")

        return fixes

    def fix_indentation_issues(self, content: str) -> str:
        """Fix indentation problems using intelligent analysis."""
        lines = content.split("\n")
        fixed_lines = []
        indent_stack = [0]  # Track indentation levels

        for i, line in enumerate(lines):
            if not line.strip():  # Empty line
                fixed_lines.append(line)
                continue

            # Calculate current indentation
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)

            # Detect logical indentation level based on code structure
            expected_indent = self._calculate_expected_indent(
                stripped, fixed_lines, indent_stack
            )

            if current_indent != expected_indent:
                # Fix the indentation
                fixed_line = " " * expected_indent + stripped
                fixed_lines.append(fixed_line)
                self.fixes_applied.append(
                    f"Line {i+1}: Fixed indent from {current_indent} to {expected_indent}"
                )
            else:
                fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def _calculate_expected_indent(
        self, stripped_line: str, previous_lines: List[str], indent_stack: List[int]
    ) -> int:
        """Calculate expected indentation based on code structure."""

        # Check if this line starts a new block
        if any(
            stripped_line.startswith(keyword)
            for keyword in [
                "def ",
                "class ",
                "if ",
                "for ",
                "while ",
                "with ",
                "try:",
                "except",
            ]
        ):
            if stripped_line.endswith(":"):
                # This line starts a new block, next line should be indented
                current_level = indent_stack[-1]
                return current_level

        # Check if this line is inside a block
        if previous_lines:
            prev_line = previous_lines[-1].strip()
            if prev_line.endswith(":"):
                # Previous line started a block, indent this line
                new_level = indent_stack[-1] + 4
                indent_stack.append(new_level)
                return new_level

        # Check if this line ends a block
        if any(
            stripped_line.startswith(keyword)
            for keyword in [
                "else:",
                "elif ",
                "except:",
                "finally:",
                "return",
                "break",
                "continue",
            ]
        ):
            # Same level as current block
            return indent_stack[-1]

        # Default: maintain current indentation level
        return indent_stack[-1] if indent_stack else 0

    def fix_string_literals(self, content: str) -> str:
        """Fix unterminated string literals and quote issues."""

        # Fix common string literal issues
        fixes = [
            # Fix corrupted docstrings with extra periods
            (r'"""([^"]*?)"""\s*\.', r'"""\1"""'),
            # Fix unterminated triple quotes
            (r'"""([^"]*?)$', r'"""\1"""'),
            # Fix missing closing quotes
            (r"'([^']*?)$", r"'\1'"),
            (r'"([^"]*?)$', r'"\1"'),
        ]

        fixed_content = content
        for pattern, replacement in fixes:
            old_content = fixed_content
            fixed_content = re.sub(
                pattern, replacement, fixed_content, flags=re.MULTILINE
            )
            if fixed_content != old_content:
                self.fixes_applied.append(f"Fixed string literal: {pattern}")

        return fixed_content

    def fix_file(self, file_path: Path) -> Tuple[bool, str]:
        """Fix a single Python file with comprehensive error handling."""

        print(f"\n🔧 Analyzing: {file_path}")

        analysis = self.analyze_file(file_path)

        if analysis["valid"]:
            print(f"✅ {file_path}: Already valid")
            return True, analysis["content"]

        print(f"❌ {file_path}: Found errors")
        for error in analysis["errors"]:
            print(f"   - {error}")

        # Apply fixes progressively
        content = analysis["content"]
        original_content = content

        # Fix 1: String literals
        content = self.fix_string_literals(content)

        # Fix 2: Indentation
        content = self.fix_indentation_issues(content)

        # Fix 3: Try to parse again
        try:
            ast.parse(content)
            print(f"✅ {file_path}: Successfully fixed!")

            if self.dry_run:
                print(f"🔍 DRY RUN - Changes for {file_path}:")
                self._show_diff(original_content, content)
                return True, content
            else:
                # Write the fixed content
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"💾 {file_path}: Fixed and saved")
                return True, content

        except SyntaxError as e:
            print(f"❌ {file_path}: Still has errors after fixes")
            print(f"   - Line {e.lineno}: {e.msg}")
            return False, content

    def _show_diff(self, original: str, fixed: str):
        """Show a simple diff of changes."""
        orig_lines = original.split("\n")
        fixed_lines = fixed.split("\n")

        max_lines = max(len(orig_lines), len(fixed_lines))
        changes_shown = 0

        for i in range(max_lines):
            orig_line = orig_lines[i] if i < len(orig_lines) else ""
            fixed_line = fixed_lines[i] if i < len(fixed_lines) else ""

            if orig_line != fixed_line and changes_shown < 10:  # Limit output
                print(f"   Line {i+1}:")
                print(f"   - {repr(orig_line)}")
                print(f"   + {repr(fixed_line)}")
                changes_shown += 1

        if changes_shown == 10:
            print("   ... (showing first 10 changes)")

    def fix_project(self, project_path: Path = Path(".")) -> Dict[str, bool]:
        """Fix all Python files in a project."""

        print("🚀 AST-Powered Syntax Fixer")
        print(f"📁 Project: {project_path.absolute()}")
        print(f"🔍 Mode: {'DRY RUN' if self.dry_run else 'APPLY FIXES'}")
        print("=" * 60)

        # Find all Python files
        python_files = list(project_path.rglob("*.py"))

        # Exclude certain directories
        excluded_dirs = {".git", "__pycache__", ".venv", "build", "dist"}
        python_files = [
            f
            for f in python_files
            if not any(part in excluded_dirs for part in f.parts)
        ]

        print(f"📋 Found {len(python_files)} Python files")

        results = {}
        fixed_count = 0

        for file_path in python_files:
            success, content = self.fix_file(file_path)
            results[str(file_path)] = success
            if success:
                fixed_count += 1

        print("\n" + "=" * 60)
        print(
            f"📊 Results: {fixed_count}/{len(python_files)} files processed successfully"
        )

        if self.fixes_applied:
            print(f"🔧 Applied {len(self.fixes_applied)} fixes:")
            for fix in self.fixes_applied[:10]:  # Show first 10
                print(f"   - {fix}")
            if len(self.fixes_applied) > 10:
                print(f"   ... and {len(self.fixes_applied) - 10} more")

        return results


def main():
    """Main function with CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="AST-Powered Python Syntax Fixer")

    # Create mutually exclusive group for dry-run vs apply
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes (SAFE)",
    )
    mode_group.add_argument(
        "--apply",
        action="store_true",
        help="Actually apply fixes to files (DESTRUCTIVE)",
    )

    parser.add_argument("--file", type=Path, help="Fix a specific file")
    parser.add_argument(
        "--project", type=Path, default=Path("."), help="Project directory to fix"
    )

    args = parser.parse_args()

    # Explicit dry-run mode selection
    fixer = SyntaxFixer(dry_run=args.dry_run)

    if args.file:
        success, content = fixer.fix_file(args.file)
        sys.exit(0 if success else 1)
    else:
        results = fixer.fix_project(args.project)
        all_success = all(results.values())
        sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
