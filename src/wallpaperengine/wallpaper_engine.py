"""Core wallpaper engine functionality."""

import logging
import os
import random
import subprocess  # nosec


class WallpaperEngine:
    """Core wallpaper engine for managing wallpaper processes.

    Handles wallpaper discovery, process management, and system integration.
    """

    def __init__(self):
        """Initialize the wallpaper engine with system detection and path finding."""
        self.log = logging.getLogger("WallpaperEngine")

        # Check for Wayland compatibility
        if self._is_wayland():
            self.log.error(
                "WAYLAND DETECTED - Linux Wallpaper Engine is NOT compatible with Wayland!"
            )
            self.log.error("Please switch to X11 session or the wallpapers will not work properly.")

        # Initialize system paths and settings
        self.display = self._detect_display()
        self.wpe_path = self._find_wpe_path()
        self.wallpaper_dir = self._find_wallpaper_dir()

        # Track current state
        self.current_wallpaper = None
        self.current_process = None  # Track current wallpaper process

    def _is_wayland(self):
        """Check if running under Wayland display server."""
        return (
            os.environ.get("WAYLAND_DISPLAY") is not None
            or os.environ.get("XDG_SESSION_TYPE") == "wayland"
        )

    def _detect_display(self):
        """Detect primary display using xrandr."""
        try:
            result = subprocess.run(  # nosec
                ["xrandr", "--query"], capture_output=True, text=True, check=False
            )
            if result.stdout:
                # Parse xrandr output for connected displays
                for line in result.stdout.split("\n"):
                    if " connected " in line:
                        display = line.split()[0]
                        self.log.info(f"Using display: {display}")
                        return display
        except Exception as e:
            self.log.error(f"Display detection failed: {e}")
        return "default"

    def _find_wpe_path(self):
        """Find linux-wallpaperengine executable."""
        common_paths = [
            # User home directories
            "~/linux-wallpaperengine/build/linux-wallpaperengine",
            "~/linux-wallpaperengine/build/output/linux-wallpaperengine",
            "~/src/linux-wallpaperengine/build/linux-wallpaperengine",
            "~/src/linux-wallpaperengine/build/output/linux-wallpaperengine",
            "~/Documents/linux-wallpaperengine/build/linux-wallpaperengine",
            "~/Documents/linux-wallpaperengine/build/output/linux-wallpaperengine",
            "~/Documents/Cursor/LWPE/linux-wallpaperengine/build/output/linux-wallpaperengine",
            "~/Projects/linux-wallpaperengine/build/linux-wallpaperengine",
            "~/Projects/linux-wallpaperengine/build/output/linux-wallpaperengine",
            # Relative paths
            "../linux-wallpaperengine/build/linux-wallpaperengine",
            "../linux-wallpaperengine/build/output/linux-wallpaperengine",
            # System paths
            "/usr/local/bin/linux-wallpaperengine",
            "/usr/bin/linux-wallpaperengine",
        ]

        for path in common_paths:
            full_path = os.path.expanduser(path)
            if os.path.isfile(full_path):
                self.log.info(f"Found WPE at: {full_path}")
                return full_path
        return None

    def _find_wallpaper_dir(self):
        """Find Steam Workshop wallpaper directory."""
        common_paths = [
            "~/.steam/steam/steamapps/workshop/content/431960",
            "~/.steam/debian-installation/steamapps/workshop/content/431960",
            "~/.local/share/Steam/steamapps/workshop/content/431960",
        ]

        for path in common_paths:
            full_path = os.path.expanduser(path)
            if os.path.isdir(full_path):
                self.log.info(f"Found wallpapers at: {full_path}")
                return full_path
        return None

    def get_wallpaper_list(self):
        """Get list of available wallpaper IDs."""
        if not self.wallpaper_dir:
            return []

        try:
            # Get all numeric directory names (wallpaper IDs)
            wallpapers = [d for d in os.listdir(self.wallpaper_dir) if d.isdigit()]
            self.log.info(f"Found {len(wallpapers)} wallpapers")
            return sorted(wallpapers)
        except Exception as e:
            self.log.error(f"Error reading wallpaper directory: {e}")
            return []

    def get_random_wallpaper(self):
        """Select a random wallpaper ID."""
        wallpapers = self.get_wallpaper_list()
        if wallpapers:
            return random.choice(wallpapers)  # nosec
        return None

    def get_next_wallpaper(self, current_id=None):
        """Get next wallpaper ID in sequence."""
        wallpapers = self.get_wallpaper_list()
        if not wallpapers:
            return None

        if not current_id:
            current_id = self.current_wallpaper

        try:
            current_idx = wallpapers.index(current_id)
            next_idx = (current_idx + 1) % len(wallpapers)
            return wallpapers[next_idx]
        except ValueError:
            return wallpapers[0]

    def get_previous_wallpaper(self, current_id=None):
        """Get previous wallpaper ID in sequence."""
        wallpapers = self.get_wallpaper_list()
        if not wallpapers:
            return None

        if not current_id:
            current_id = self.current_wallpaper

        try:
            current_idx = wallpapers.index(current_id)
            prev_idx = (current_idx - 1) % len(wallpapers)
            return wallpapers[prev_idx]
        except ValueError:
            return wallpapers[-1] if wallpapers else None

    def run_wallpaper(self, wallpaper_id, **options):
        """Run wallpaper with specified options."""
        if not all([self.wpe_path, self.display, wallpaper_id]):
            self.log.error(
                f"Missing components - path: {self.wpe_path}, "
                f"display: {self.display}, id: {wallpaper_id}"
            )
            return False, None

        try:
            # Stop any running wallpaper first
            self.log.info("Stopping current wallpaper...")
            self.stop_wallpaper()

            # Save current directory
            original_dir = os.getcwd()
            self.log.debug(f"Original directory: {original_dir}")

            # Change to WPE directory
            wpe_dir = os.path.dirname(self.wpe_path)
            self.log.info(f"Changing to WPE directory: {wpe_dir}")
            os.chdir(wpe_dir)

            # Build command
            cmd = [self.wpe_path]

            # Add common options
            if options.get("fps"):
                cmd.extend(["--fps", str(options["fps"])])
            if options.get("mute"):
                cmd.append("--silent")
            if "volume" in options:
                cmd.extend(["--volume", str(int(options["volume"]))])
            if options.get("no_automute"):
                cmd.append("--noautomute")
            if options.get("no_audio_processing"):
                cmd.append("--no-audio-processing")
            if options.get("no_fullscreen_pause"):
                cmd.append("--no-fullscreen-pause")
            if options.get("disable_mouse"):
                cmd.append("--disable-mouse")
            if options.get("scaling"):
                cmd.extend(["--scaling", options["scaling"]])
            if options.get("clamping"):
                cmd.extend(["--clamping", options["clamping"]])

            # Add custom arguments if enabled
            if options.get("enable_custom_args") and options.get("custom_args"):
                custom_args = options["custom_args"].split()
                cmd.extend(custom_args)

            # Add wallpaper path
            wallpaper_path = os.path.join(self.wallpaper_dir, wallpaper_id)
            cmd.append(wallpaper_path)

            # Set environment for LD_PRELOAD if enabled
            env = os.environ.copy()
            if options.get("enable_ld_preload"):
                libcef_path = os.path.join(wpe_dir, "libcef.so")
                if os.path.exists(libcef_path):
                    env["LD_PRELOAD"] = libcef_path

            self.log.info(f"Running command: {' '.join(cmd)}")

            # Start wallpaper process
            self.current_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
            )

            self.current_wallpaper = wallpaper_id
            self.log.info(f"Started wallpaper {wallpaper_id} (PID: {self.current_process.pid})")

            # Restore original directory
            os.chdir(original_dir)

            return True, cmd

        except Exception as e:
            self.log.error(f"Failed to run wallpaper {wallpaper_id}: {e}")
            # Restore original directory on error
            try:
                os.chdir(original_dir)
            except OSError:
                pass
            return False, None

    def stop_wallpaper(self):
        """Stop currently running wallpaper."""
        try:
            if self.current_process and self.current_process.poll() is None:
                self.log.info(f"Terminating wallpaper process (PID: {self.current_process.pid})")
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.log.warning("Process didn't terminate, killing...")
                    self.current_process.kill()
                    self.current_process.wait()

            self.current_process = None
            self.current_wallpaper = None
            return True

        except Exception as e:
            self.log.error(f"Error stopping wallpaper: {e}")
            return False
