"""CI smoke tests for the standalone GTK script.

Avoids importing ``linux-wallpaperengine-gtk`` (GI/GTK, displays): only syntax and
bytecode compilation — the same guarantees as ``python -m py_compile``.
"""

from __future__ import annotations

import pathlib
import py_compile
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAIN = ROOT / "linux-wallpaperengine-gtk.py"
PROBE = ROOT / "wallpaper_process_probe.py"


def test_main_script_exists():
    assert MAIN.is_file(), f"Expected {MAIN}"


def test_probe_module_exists():
    assert PROBE.is_file(), f"Expected {PROBE}"


def test_main_script_byte_compiles():
    py_compile.compile(str(MAIN), doraise=True)


def test_probe_module_byte_compiles():
    py_compile.compile(str(PROBE), doraise=True)


def test_py_compile_cli_matches_byte_compile():
    subprocess.run(
        [sys.executable, "-m", "py_compile", str(MAIN), str(PROBE)],
        cwd=str(ROOT),
        check=True,
    )
