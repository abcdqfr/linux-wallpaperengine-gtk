"""Tests for the Linux Wallpaper Engine GTK Frontend."""

from unittest.mock import patch

import pytest


def test_wallpaper_engine_initialization():
        """Test WallpaperEngine can be initialized."""

from wallpaperengine.wallpaper_engine import WallpaperEngine

    with patch("os.environ.get") as mock_env:
        mock_env.return_value = None  # Not Wayland
        engine = WallpaperEngine()
        assert engine is not None


def test_wallpaper_engine_wayland_detection():
        """Test Wayland detection."""

from wallpaperengine.wallpaper_engine import WallpaperEngine

    with patch("os.environ.get") as mock_env:
        mock_env.side_effect = lambda key: "wayland" if key == "XDG_SESSION_TYPE" else None
        engine = WallpaperEngine()
        # Should log error but not crash
        assert engine is not None


def test_wallpaper_engine_get_wallpaper_list():
        """Test wallpaper list retrieval."""

from wallpaperengine.wallpaper_engine import WallpaperEngine

    with patch("os.environ.get") as mock_env, patch("os.path.exists") as mock_exists, patch(
        "os.listdir"
    ) as mock_listdir:
        mock_env.return_value = None
        mock_exists.return_value = True
        mock_listdir.return_value = ["123456", "789012", "not_a_number"]

        engine = WallpaperEngine()
        engine.wallpaper_dir = "/fake/path"

        wallpapers = engine.get_wallpaper_list()
        assert isinstance(wallpapers, list)
        # Should filter out non-numeric directories
        assert "123456" in wallpapers
        assert "789012" in wallpapers
        assert "not_a_number" not in wallpapers


def test_wallpaper_engine_stop_wallpaper():
        """Test wallpaper stopping functionality."""

from wallpaperengine.wallpaper_engine import WallpaperEngine

    with patch("os.environ.get") as mock_env, patch("subprocess.run") as mock_run:
        mock_env.return_value = None
        mock_run.return_value.returncode = 1  # No processes found

        engine = WallpaperEngine()
        result = engine.stop_wallpaper()
        assert result is True


def test_wallpaper_engine_display_detection():
        """Test display detection."""
    from wallpaperengine.wallpaper_engine import WallpaperEngine

    with patch("os.environ.get") as mock_env, patch("subprocess.run") as mock_run:
        mock_env.return_value = None
        mock_run.return_value.stdout = "HDMI-0\n"
        mock_run.return_value.returncode = 0

        engine = WallpaperEngine()
        assert engine.display == "HDMI-0"


if __name__ == "__main__":
    pytest.main([__file__])
