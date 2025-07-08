"""Test configuration and shared fixtures."""

# Mock GTK imports for testing
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest

sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.GdkPixbuf"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()


@pytest.fixture
def tmp_config(tmp_path: Path) -> Generator[Path, None, None]:
    """Create temporary config directory."""
    config_dir = tmp_path / ".config" / "linux-wallpaperengine-gtk"
    config_dir.mkdir(parents=True)
    yield config_dir


@pytest.fixture
def mock_display() -> Generator[str, None, None]:
    """Mock display detection."""
    yield "DISPLAY-1"


@pytest.fixture
def mock_wallpapers(tmp_path: Path) -> Generator[Path, None, None]:
    """Create mock wallpaper directory."""
    wallpaper_dir = tmp_path / "wallpapers"
    wallpaper_dir.mkdir()
    for wid in ["123", "456", "789"]:
        (wallpaper_dir / wid).mkdir()
    yield wallpaper_dir
