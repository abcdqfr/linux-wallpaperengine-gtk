#!/usr/bin/env python3
"""Version-based pre-commit strictness checker.

This script reads the version from pyproject.toml and conditionally
enables or disables pre-commit hooks based on the version number.

Version ranges:
- 0.1.x: Very lenient (basic checks only)
- 0.5.x: Moderate (add type checking, warnings)
- 0.9.x: Strict (add docstring style, strict markdown)
- 1.0+: Very strict (all checks enabled)
"""

import os
import sys
from pathlib import Path

# Try to import toml (built-in in Python 3.11+)
try:
    import tomllib
    _TOML_IS_BUILTIN = True
except ImportError:
    try:
        import toml as tomllib
        _TOML_IS_BUILTIN = False
    except ImportError:
        print("Error: No TOML parser available. Install 'toml' package or use Python 3.11+")
        sys.exit(1)


def get_version():
    """Get version from pyproject.toml."""
    try:
        if _TOML_IS_BUILTIN:
            with open("pyproject.toml", "rb") as f:
                data = tomllib.load(f)
        else:
            with open("pyproject.toml", "r") as f:
                data = tomllib.load(f)
        return data["project"]["version"]
    except (FileNotFoundError, KeyError, Exception) as e:
        print(f"Warning: Could not read version from pyproject.toml: {e}")
        return "0.1.0"


def parse_version(version):
    """Parse version string into major, minor, patch."""
    try:
        parts = version.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return major, minor, patch
    except (ValueError, IndexError):
        print(f"Warning: Invalid version format: {version}")
        return 0, 1, 0


def get_strictness_level(version):
    """Determine strictness level based on version."""
    major, minor, _ = parse_version(version)

    if major == 0:
        if minor < 5:
            return "very_lenient"
        elif minor < 9:
            return "moderate"
        else:
            return "strict"
    else:
        return "very_strict"


def should_enable_hook(hook_name, strictness_level):
    """Determine if a hook should be enabled based on strictness level."""

    # Always enabled hooks (core functionality)
    always_enabled = {
        "ruff", "ruff-format", "black", "bandit",
        "prettier", "trailing-whitespace", "end-of-file-fixer",
        "check-yaml", "check-added-large-files", "check-merge-conflict",
        "check-case-conflict", "check-json", "check-toml",
        "debug-statements", "name-tests-test", "requirements-txt-fixer",
        "fix-byte-order-marker", "shellcheck", "yamllint", "commitlint"
    }

    if hook_name in always_enabled:
        return True

    # Conditional hooks based on strictness
    if strictness_level == "very_lenient":
        # Only basic checks
        return False

    elif strictness_level == "moderate":
        # Add type checking but be lenient
        moderate_hooks = {"mypy"}
        return hook_name in moderate_hooks

    elif strictness_level == "strict":
        # Add docstring and markdown checks
        strict_hooks = {"mypy", "pydocstyle", "markdownlint"}
        return hook_name in strict_hooks

    elif strictness_level == "very_strict":
        # All hooks enabled
        return True

    return False


def main():
    """Main function to check version and set strictness."""
    version = get_version()
    strictness = get_strictness_level(version)

    print(f"Version: {version}")
    print(f"Strictness level: {strictness}")

    # Set environment variable for other hooks to read
    os.environ["PRECOMMIT_STRICTNESS"] = strictness

    # Check if we should run specific hooks
    hook_name = os.environ.get("PRE_COMMIT_HOOK_NAME", "")

    if hook_name and not should_enable_hook(hook_name, strictness):
        print(f"Skipping {hook_name} due to strictness level {strictness}")
        sys.exit(0)

    # For the version checker itself, always succeed
    if os.environ.get("PRE_COMMIT_HOOK_NAME") == "version-based-strictness":
        print("Version-based strictness check passed")
        sys.exit(0)

    # For other hooks, let them run normally
    sys.exit(0)


if __name__ == "__main__":
    main()
