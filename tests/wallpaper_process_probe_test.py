"""Behavioral tests for timer-free subprocess / PID probing (no GTK)."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

from wallpaper_process_probe import pid_exists, wallpaper_subprocess_running

ROOT = Path(__file__).resolve().parents[1]


def test_pid_exists_current_process():
    assert pid_exists(os.getpid()) is True


def test_pid_exists_non_positive_false():
    assert pid_exists(0) is False
    assert pid_exists(-1) is False


def test_wallpaper_subprocess_running_after_child_exits_false():
    proc = subprocess.Popen(
        [sys.executable, "-c", "raise SystemExit(3)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    assert proc.wait() == 3
    assert wallpaper_subprocess_running(proc) is False


def test_wallpaper_subprocess_running_long_running_child_true():
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        assert wallpaper_subprocess_running(proc) is True
        assert proc.poll() is None
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def test_run_wallpaper_has_no_time_sleep():
    """Guard the regression where startup used a fixed delay instead of kernel facts."""
    path = ROOT / "linux-wallpaperengine-gtk.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "WallpaperEngine":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "run_wallpaper":
                    for sub in ast.walk(item):
                        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                            if (
                                sub.func.attr == "sleep"
                                and isinstance(sub.func.value, ast.Name)
                                and sub.func.value.id == "time"
                            ):
                                pytest.fail(
                                    "WallpaperEngine.run_wallpaper must not call time.sleep — "
                                    "use wallpaper_subprocess_running / poll / /proc evidence"
                                )
                    return
    pytest.fail("WallpaperEngine.run_wallpaper not found in AST")
