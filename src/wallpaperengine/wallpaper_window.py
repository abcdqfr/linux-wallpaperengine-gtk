"""GTK UI management for wallpaper window display."""

import json
import logging
import os

from gi.repository import GLib, Gtk

from .wallpaper_engine import WallpaperEngine


class WallpaperWindow(Gtk.Window):
    """Main application window for Linux Wallpaper Engine GTK.

    Provides the primary user interface for browsing, selecting,
    and managing wallpapers with comprehensive controls and settings.
    """

    def __init__(self, initial_settings=None):
        """Initialize the main application window.

        Args:
            initial_settings: Optional dictionary of initial settings to
                override defaults.
        """
        super().__init__(title="Linux Wallpaper Engine")
        self.set_default_size(800, 600)

        # Initialize logging
        self.log = logging.getLogger("WallpaperWindow")

        # Initialize wallpaper engine
        self.engine = WallpaperEngine()

        # Load settings with optional overrides
        self.load_settings()
        if initial_settings:
            self.settings.update(initial_settings)

        # Setup UI
        self._setup_ui()

        # Connect signals
        self.connect("destroy", self.on_destroy)

        # Check initial setup
        GLib.idle_add(self.check_initial_setup)

    def _setup_ui(self):
        """Setup main UI components."""
        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.main_box)

        # Create toolbar
        self._create_toolbar()

        # Create main content area (placeholder)
        self.content_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.pack_start(self.content_area, True, True, 0)

        # Create status bar
        self.statusbar = Gtk.Statusbar()
        self.command_context = self.statusbar.get_context_id("command")
        self.status_label = Gtk.Label(text="Ready")
        self.main_box.pack_end(self.statusbar, False, False, 0)

    def _create_toolbar(self):
        """Create the toolbar with controls."""
        # TODO: Implement toolbar creation
        # Will handle preview size scale changes
        # Load and display wallpaper previews
        # Reload wallpapers with current preview size
        self.load_wallpapers()

    def load_wallpapers(self):
        """Load and display wallpaper previews."""
        # TODO: Implement wallpaper loading
        self.log.info("Loading wallpapers...")

    def update_current_wallpaper(self, wallpaper_id):
        """Update UI to reflect current wallpaper."""
        # Update status
        self.status_label.set_text(f"Current: {wallpaper_id}")

    def on_destroy(self, window):
        """Clean up before exit."""
        self.log.info("Shutting down...")
        # Don't stop wallpaper on exit - let it continue running
        Gtk.main_quit()

    def load_settings(self):
        """Load settings from config file."""
        config_dir = os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
        config_file = os.path.join(config_dir, "settings.json")

        # Default settings
        self.settings = {
            "fps": 30,
            "volume": 100,
            "mute": False,
            "quality": "medium",
        }

        try:
            if os.path.exists(config_file):
                with open(config_file) as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
                self.log.info("Settings loaded successfully")
        except Exception as e:
            self.log.error(f"Failed to load settings: {e}")

    def save_settings(self):
        """Save settings to config file."""
        config_dir = os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
        config_file = os.path.join(config_dir, "settings.json")

        try:
            os.makedirs(config_dir, exist_ok=True)
            with open(config_file, "w") as f:
                json.dump(self.settings, f, indent=2)
            self.log.info("Settings saved successfully")
        except Exception as e:
            self.log.error(f"Failed to save settings: {e}")

    def check_initial_setup(self):
        """Check if initial setup is needed."""
        # TODO: Implement initial setup check
        return False
