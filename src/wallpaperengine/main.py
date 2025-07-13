"""Main module for Linux Wallpaper Engine GTK.

Extracted from mature monolith v0.2.1.
"""

import argparse
import logging

from gi.repository import Gtk

from .wallpaper_window import WallpaperWindow


def main():
    """Main entry point for Linux Wallpaper Engine GTK."""
    # Setup logging with more verbose output
    logging.basicConfig(
        level=logging.DEBUG,  # Changed from INFO to DEBUG
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler("wallpaper-engine.log"),  # File output
        ],
    )

    logging.info("Starting Linux Wallpaper Engine GTK...")

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Linux Wallpaper Engine GTK")
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--volume", type=int, default=100)
    parser.add_argument("--mute", action="store_true")
    parser.add_argument("--disable-mouse", action="store_true")
    parser.add_argument("--no-automute", action="store_true")
    parser.add_argument("--no-audio-processing", action="store_true")
    parser.add_argument("--no-fullscreen-pause", action="store_true")
    parser.add_argument(
        "--scaling", choices=["default", "stretch", "fit", "fill"], default="default"
    )
    parser.add_argument("--clamping", choices=["clamp", "border", "repeat"], default="clamp")
    args = parser.parse_args()

    # Create and show window
    win = WallpaperWindow(
        initial_settings={
            "fps": args.fps,
            "volume": args.volume,
            "mute": args.mute,
            "mouse_enabled": args.disable_mouse,
            "auto_rotation": False,
            "rotation_interval": 15,
            "no_automute": args.no_automute,
            "no_audio_processing": args.no_audio_processing,
            "no_fullscreen_pause": args.no_fullscreen_pause,
            "scaling": args.scaling,
            "clamping": args.clamping,
        }
    )
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

    # Start GTK main loop
    logging.info("Entering GTK main loop")
    Gtk.main()
