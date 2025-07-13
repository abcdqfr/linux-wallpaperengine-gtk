#!/usr/bin/env python3
"""
Automatic docstring fixer for pydocstyle violations.
Fixes the most common issues: D415 (missing periods) and D212 (formatting).
"""

import re
from pathlib import Path


def fix_docstring_periods(content):
    """Fix D415 violations by adding periods to docstring first lines."""
    # Pattern to match docstrings that don't end with punctuation
    pattern = r'"""(.*?)(?<!\.|\?|\!)(?=\s*""")'

    def add_period(match):
        docstring = match.group(1).strip()
        if docstring and not docstring.endswith((".", "?", "!")):
            return f'"""{docstring}."""'
        return match.group(0)

    return re.sub(pattern, add_period, content)


def fix_module_docstrings(content):
    """Fix D212 violations by ensuring proper module docstring formatting."""
    # Pattern to match module docstrings that need fixing
    pattern = r'"""(.*?)\n(.*?)"""'

    def fix_module_doc(match):
        first_line = match.group(1).strip()
        rest = match.group(2).strip()

        if first_line and rest:
            # Add period to first line if missing
            if not first_line.endswith((".", "?", "!")):
                first_line += "."

            # Ensure proper spacing
            return f'"""{first_line}\n\n{rest}"""'

    return re.sub(pattern, fix_module_doc, content, flags=re.DOTALL)


def fix_blank_lines_after_docstrings(content):
    """Fix D202 violations by removing extra blank lines after docstrings."""
    # Pattern to match docstrings followed by multiple blank lines
    pattern = r'"""*?"""\n\n+'

    def fix_blank_lines(match):
        return match.group(0).rstrip("\n") + "\n"

    return re.sub(pattern, fix_blank_lines, content, flags=re.DOTALL)


def process_file(file_path):
    """Process a single file and fix docstring issues."""
    print(f"Processing {file_path}...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Apply fixes
    content = fix_docstring_periods(content)
    content = fix_module_docstrings(content)
    content = fix_blank_lines_after_docstrings(content)

    # Write back if changed
    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ Fixed {file_path}")
        return True
    else:
        print(f"  ⏭️  No changes needed for {file_path}")
        return False


def main():
    """Main function to process all Python files."""
    # Files to process based on pydocstyle output
    files_to_fix = [
        "src/wallpaperengine/settings_dialog.py",
        "src/wallpaperengine/wallpaper_context_menu.py",
        "src/wallpaperengine/wallpaper_engine.py",
        "src/wallpaperengine/wallpaper_window.py",
        "scripts/build_monolith.py",
        "scripts/reverse_demonolith.py",
        "tests/pytest_suite_test.py",
    ]

    fixed_count = 0
    total_count = len(files_to_fix)

    for file_path in files_to_fix:
        if Path(file_path).exists():
            if process_file(file_path):
                fixed_count += 1
        else:
            print(f"  ❌ File not found: {file_path}")

    print(f"\n🎉 Fixed {fixed_count}/{total_count} files!")

    if fixed_count > 0:
        print("\nNow run: pre-commit run pydocstyle --all-files")
    else:
        print("\nNo files needed fixing.")


if __name__ == "__main__":
    main()
