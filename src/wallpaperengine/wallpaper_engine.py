

import logging
import os
import random
import subprocess  # nosec
import time


class WallpaperEngine:
    """Core wallpaper engine functionality for managing and running wallpapers.

Handles wallpaper detection, execution, and lifecycle management
    for the Linux Wallpaper Engine GTK application."""
    def __init__(self):
        """Initialize the wallpaper engine with system detection and path finding."""

self.log = logging.getLogger("WallpaperEngine")

        # Check for Wayland compatibility
        if self._is_wayland():
            self.log.error(
                "WAYLAND DETECTED - Linux Wallpaper Engine is NOT compatible with Wayland!"
            )
            self.log.error("Please switch to X11 session or the wallpapers will not work properly.")

        self.display = self._detect_display()
        self.wpe_path = self._find_wpe_path()
        self.wallpaper_dir = self._find_wallpaper_dir()
        self.current_wallpaper = None
        self.current_process = None  # Track current wallpaper process

    def _detect_display(self):
        """Detect primary display using xrandr.Find linux-wallpaperengine executable.Find Steam Workshop wallpaper directory.Get list of available wallpaper IDs.Select a random wallpaper ID.Get next wallpaper ID in sequence.Get previous wallpaper ID in sequence.Run wallpaper with specified options.Stop currently running wallpaper.Check if running under Wayland."""
        return (
            os.environ.get("WAYLAND_DISPLAY") is not None
            or os.environ.get("XDG_SESSION_TYPE") == "wayland"
        )
