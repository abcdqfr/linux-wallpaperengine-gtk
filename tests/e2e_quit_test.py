from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "linux-wallpaperengine-gtk.py"


def test_e2e_quit_with_settings_open_under_xvfb(tmp_path: Path):
    """
    End-to-end regression: quitting while SettingsDialog.run() is active must not hang.

    This runs the real script under Xvfb so it has a display server, but requires no
    user interaction.
    """
    # pre-commit's pytest env may not have PyGObject; skip rather than failing the gate.
    try:
        import gi  # noqa: F401
    except Exception:
        pytest.skip("PyGObject (gi) not available in this test environment")

    if os.environ.get("CI") and not shutil.which("xvfb-run"):
        # CI images should install it; if not, make it explicit.
        raise AssertionError("xvfb-run not found; install xvfb for e2e quit test")

    if not shutil.which("xvfb-run"):
        # Local dev may not have it; skip rather than failing.
        return

    # Isolate from the developer's real settings.json so this test doesn't try to
    # enumerate a huge Workshop library (which can keep the loop busy and mask quit).
    # Use a tiny fixture wallpaper dir and a stub engine binary.
    home = tmp_path / "home"
    home.mkdir()

    cfg = home / ".config" / "linux-wallpaperengine-gtk"
    cfg.mkdir(parents=True, exist_ok=True)
    fixture_root = home / "fixture" / "431960" / "123"
    fixture_root.mkdir(parents=True, exist_ok=True)
    (fixture_root / "project.json").write_text('{"file":"video.mp4"}', encoding="utf-8")
    (fixture_root / "video.mp4").write_bytes(b"")
    stub_engine = home / "stub-engine"
    stub_engine.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
    stub_engine.chmod(0o755)

    (cfg / "settings.json").write_text(
        (
            "{\n"
            f'  "wpe_path": "{stub_engine}",\n'
            f'  "wallpaper_dir": "{home / "fixture" / "431960"}"\n'
            "}\n"
        ),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["XDG_CACHE_HOME"] = str(home / ".cache")

    # Use timeout(1) to ensure we kill the full Xvfb+app tree on hangs.
    subprocess.run(
        [
            "timeout",
            "15s",
            "xvfb-run",
            "-a",
            sys.executable,
            str(MAIN),
            "--e2e-quit-test",
        ],
        cwd=str(ROOT),
        env=env,
        check=True,
    )

