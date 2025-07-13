#!/usr/bin/env python3
"""
Surgical docstring fixer - only fixes D415 violations without breaking syntax.
"""

import re
from pathlib import Path


def fix_d415_violations(content):
    """Fix only D415 violations by adding periods to docstring first lines."""
    # Pattern to match docstrings that don't end with punctuation
    # This is MUCH more careful - only matches single-line docstrings
    pattern = r'"""(.*?)(?<!\.|\?|\!)(?=\s*""")'

    def add_period(match):
        docstring = match.group(1).strip()
        if docstring and not docstring.endswith((".", "?", "!")):
            return f'"""{docstring}."""'
        return match.group(0)

    return re.sub(pattern, add_period, content)


def process_file(file_path):
    """Process a single file and fix ONLY D415 issues."""
    print(f"Processing {file_path}...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Apply ONLY D415 fixes
    content = fix_d415_violations(content)

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
    """Main function to process all Python files with surgical precision."""
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
