#!/usr/bin/env python3
"""
Fix the mess I created with my aggressive regex.
This script will:
1. Fix the broken docstring syntax (extra periods, triple quotes)
2. Add periods properly to D415 violations
3. Learn from my mistakes
"""

import re
from pathlib import Path


def fix_broken_docstrings(content):
    """Fix the syntax errors I created with my aggressive regex."""
    # Fix extra periods at the end of docstrings
    content = re.sub(r'"""(.*?)\.\."""', r'"""\1."""', content)

    # Fix triple quotes (my regex created """")
    content = re.sub(r'""""""', r'"""', content)

    # Fix broken function definitions with docstrings
    content = re.sub(r'def (\w+\([^)]*\)):"""([^"]*)"""', r'def \1:\n        """\2"""', content)

    return content


def add_periods_carefully(content):
    """Add periods to D415 violations CAREFULLY."""
    # Only target single-line docstrings that don't end with punctuation
    # This is MUCH more surgical than my previous attempt
    pattern = r'"""(.*?)(?<!\.|\?|\!)(?=\s*""")'

    def add_period(match):
        docstring = match.group(1).strip()
        if docstring and not docstring.endswith((".", "?", "!")):
            return f'"""{docstring}."""'
        return match.group(0)

    return re.sub(pattern, add_period, content)


def process_file(file_path):
    """Process a single file and fix my mess."""
    print(f"Processing {file_path}...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # First, fix the broken syntax I created
    content = fix_broken_docstrings(content)

    # Then, carefully add periods to D415 violations
    content = add_periods_carefully(content)

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
    """Main function to fix my mess."""
    # Files I broke
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
    print("\nLESSON LEARNED: Always test regex on ONE LINE first!")

    if fixed_count > 0:
        print("\nNow run: pre-commit run pydocstyle --all-files")
    else:
        print("\nNo files needed fixing.")


if __name__ == "__main__":
    main()
