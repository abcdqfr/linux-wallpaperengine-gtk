

import json
import logging
import os
import threading

from gi.repository import Gdk, GdkPixbuf, GLib, Gtk

from .settings_dialog import SettingsDialog
from .wallpaper_context_menu import WallpaperContextMenu
from .wallpaper_engine import WallpaperEngine


class WallpaperWindow(Gtk.Window):
    """Main application window for Linux Wallpaper Engine GTK.

Provides the primary user interface for browsing, selecting,
    and managing wallpapers with comprehensive controls and settings."""

    def __init__(self, initial_settings=None):
        """Initialize the main application window.

Args:
            initial_settings: Optional dictionary of initial settings to override defaults."""
        super().__init__(title="Linux Wallpaper Engine")
        self.set_default_size(800, 600)

        # Initialize engine
        self.engine = WallpaperEngine()

        # Setup logging
        self.log = logging.getLogger("GUI")

        # Preview size (default 200x120)
        self.preview_width = 200
        self.preview_height = 120

        # Playlist support
        self.playlist_timeout = None
        self.playlist_active = False

        # Default settings
        self.settings = {
            "fps": 60,
            "volume": 100,
            "mute": False,
            "mouse_enabled": True,
            "auto_rotation": False,
            "rotation_interval": 15,
            "no_automute": False,
            "no_audio_processing": False,
            "no_fullscreen_pause": False,
            "scaling": "default",
            "clamping": "clamp",
            "enable_custom_args": False,
            "custom_args": "",
            "enable_ld_preload": False,
        }

        # Merge initial settings with defaults
        if initial_settings:
            self.settings.update(initial_settings)

        # Load saved settings (including paths) BEFORE anything else
        self.load_settings()

        # Initialize UI
        self._setup_ui()

        # Load wallpapers
        self.load_wallpapers()

        self.connect("destroy", self.on_destroy)

        # Add CSS provider for styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(
            b
        )
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Check if setup is needed
        GLib.idle_add(self.check_initial_setup)

    def _setup_ui(self):
        """Setup main UI components."""

# Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.main_box)

        # Toolbar
        self._create_toolbar()

        # Wallpaper grid
        scrolled = Gtk.ScrolledWindow()
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(30)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flowbox.connect("child-activated", self.on_wallpaper_selected)
        self.flowbox.connect("button-press-event", self.on_right_click)
        scrolled.add(self.flowbox)
        self.main_box.pack_start(scrolled, True, True, 0)

        # Status bar
        self.statusbar = Gtk.Statusbar()
        self.statusbar.set_margin_top(0)
        self.statusbar.set_margin_bottom(2)
        self.command_context = self.statusbar.get_context_id("command")
        self.main_box.pack_end(self.statusbar, False, False, 0)

    def _create_toolbar(self):
        """Create the toolbar with controls.Handle preview size scale changes.Load and display wallpaper previews.Reload wallpapers with current preview size."""

self.load_wallpapers()

    def highlight_current_wallpaper(self, current_box=None):
        """Update the highlight for the current wallpaper."""

# Remove highlight from all boxes
        for child in self.flowbox.get_children():
            box = child.get_child()
            box.get_style_context().remove_class("current-wallpaper")

        # Add highlight to current box
        if current_box:
            current_box.get_style_context().add_class("current-wallpaper")

    def update_current_wallpaper(self, wallpaper_id):
        """Update UI to reflect current wallpaper."""

# Update status
        self.status_label.set_text(f"Current: {wallpaper_id}")

        # Find and highlight the current wallpaper box
        for child in self.flowbox.get_children():
            box = child.get_child()
            if box.wallpaper_id == wallpaper_id:
                self.highlight_current_wallpaper(box)
                # Get the scrolled window and scroll to the child's position
                adj = child.get_parent().get_parent().get_vadjustment()
                if adj:
                    alloc = child.get_allocation()
                    adj.set_value(alloc.y - (adj.get_page_size() / 2))
                break

    def on_wallpaper_selected(self, flowbox, child):
        """Handle wallpaper selection."""

wallpaper_id = child.get_child().wallpaper_id
        self.status_label.set_text(f"Loading wallpaper {wallpaper_id}...")
        success, cmd = self._load_wallpaper(wallpaper_id)
        if success:
            self.update_current_wallpaper(wallpaper_id)
            if cmd:
                self.update_command_status(cmd)
        else:
            self.status_label.set_text("Failed to load wallpaper")

    def _load_wallpaper(self, wallpaper_id):
        """Load wallpaper with current settings."""

return self.engine.run_wallpaper(
            wallpaper_id,
            fps=self.settings["fps"],
            volume=self.settings["volume"],
            mute=self.settings["mute"],
            no_automute=self.settings["no_automute"],
            no_audio_processing=self.settings["no_audio_processing"],
            disable_mouse=self.settings["mouse_enabled"],
            no_fullscreen_pause=self.settings["no_fullscreen_pause"],
            scaling=self.settings["scaling"],
            clamping=self.settings["clamping"],
            enable_custom_args=self.settings["enable_custom_args"],
            custom_args=self.settings["custom_args"],
            enable_ld_preload=self.settings["enable_ld_preload"],
        )

    def on_prev_clicked(self, button):
        """Load previous wallpaper."""

if wallpaper_id := self.engine.get_previous_wallpaper():
            success, cmd = self._load_wallpaper(wallpaper_id)
            if success:
                self.update_current_wallpaper(wallpaper_id)
                if cmd:
                    self.update_command_status(cmd)

    def on_next_clicked(self, button):
        """Load next wallpaper."""

if wallpaper_id := self.engine.get_next_wallpaper():
            success, cmd = self._load_wallpaper(wallpaper_id)
            if success:
                self.update_current_wallpaper(wallpaper_id)
                if cmd:
                    self.update_command_status(cmd)

    def on_random_clicked(self, button):
        """Load random wallpaper."""

if wallpaper_id := self.engine.get_random_wallpaper():
            success, cmd = self._load_wallpaper(wallpaper_id)
            if success:
                self.update_current_wallpaper(wallpaper_id)
                if cmd:
                    self.update_command_status(cmd)

    def on_refresh_clicked(self, button):
        """Refresh wallpaper list."""

self.status_label.set_text("Refreshing wallpaper list...")
        self.load_wallpapers()
        self.status_label.set_text("Wallpaper list refreshed")

    def on_setup_clicked(self, button):
        """Open setup dialog for path configuration."""

dialog = SettingsDialog(self)

        # Switch to the Paths tab automatically
        notebook = dialog.get_content_area().get_children()[0]
        notebook.set_current_page(5)  # Paths tab is the 6th tab (0-indexed)

        response = dialog.run()

        if response != Gtk.ResponseType.OK:
            dialog.destroy()
            return

        try:
            # Handle path changes only
            new_wpe_path = dialog.wpe_entry.get_text().strip()
            new_wallpaper_dir = dialog.wallpaper_entry.get_text().strip()

            paths_changed = False
            if new_wpe_path != (self.engine.wpe_path or ""):
                if new_wpe_path and os.path.isfile(new_wpe_path):
                    self.engine.wpe_path = new_wpe_path
                    paths_changed = True
                    self.log.info(f"Updated wallpaper engine path: {new_wpe_path}")
                elif new_wpe_path:
                    self.status_label.set_text("Error: Invalid wallpaper engine path")
                    dialog.destroy()
                    return

            if new_wallpaper_dir != (self.engine.wallpaper_dir or ""):
                if new_wallpaper_dir and os.path.isdir(new_wallpaper_dir):
                    self.engine.wallpaper_dir = new_wallpaper_dir
                    paths_changed = True
                    self.log.info(f"Updated wallpaper directory: {new_wallpaper_dir}")
                elif new_wallpaper_dir:
                    self.status_label.set_text("Error: Invalid wallpaper directory")
                    dialog.destroy()
                    return

            # Reload wallpapers if paths changed
            if paths_changed:
                self.status_label.set_text("Reloading wallpapers...")
                self.save_settings()  # Save paths immediately
                self.load_wallpapers()
            else:
                self.status_label.set_text("No path changes made")

        except Exception as e:
            self.log.error(f"Failed to apply setup: {e}")
        finally:
            dialog.destroy()

    def on_settings_clicked(self, button):
        """Open settings dialog."""

dialog = SettingsDialog(self)
        response = dialog.run()

        if response != Gtk.ResponseType.OK:
            dialog.destroy()  # Destroy dialog first to prevent GTK warnings
            return  # Don't apply settings if cancelled

        try:
            # Save settings including paths
            settings = {
                "fps": dialog.fps_spin.get_value_as_int(),
                "volume": self.settings["volume"],  # Keep current volume
                "mute": self.settings["mute"],  # Keep current mute state
                "mouse_enabled": dialog.mouse_switch.get_active(),
                "auto_rotation": dialog.rotation_switch.get_active(),
                "rotation_interval": dialog.interval_spin.get_value_as_int(),
                "no_automute": dialog.no_automute_switch.get_active(),
                "no_audio_processing": dialog.no_audio_processing_switch.get_active(),
                "no_fullscreen_pause": dialog.no_fullscreen_pause_switch.get_active(),
                "scaling": dialog.scaling_combo.get_active_text(),
                "clamping": dialog.clamping_combo.get_active_text(),
                "enable_custom_args": dialog.custom_args_switch.get_active(),
                "custom_args": dialog.custom_args_entry.get_text().strip(),
                "enable_ld_preload": dialog.ld_preload_switch.get_active(),
            }

            # Handle path changes
            new_wpe_path = dialog.wpe_entry.get_text().strip()
            new_wallpaper_dir = dialog.wallpaper_entry.get_text().strip()

            paths_changed = False
            if new_wpe_path != (self.engine.wpe_path or ""):
                if new_wpe_path and os.path.isfile(new_wpe_path):
                    self.engine.wpe_path = new_wpe_path
                    paths_changed = True
                    self.log.info(f"Updated wallpaper engine path: {new_wpe_path}")
                elif new_wpe_path:
                    self.status_label.set_text("Error: Invalid wallpaper engine path")
                    dialog.destroy()
                    return

            if new_wallpaper_dir != (self.engine.wallpaper_dir or ""):
                if new_wallpaper_dir and os.path.isdir(new_wallpaper_dir):
                    self.engine.wallpaper_dir = new_wallpaper_dir
                    paths_changed = True
                    self.log.info(f"Updated wallpaper directory: {new_wallpaper_dir}")
                elif new_wallpaper_dir:
                    self.status_label.set_text("Error: Invalid wallpaper directory")
                    dialog.destroy()
                    return

            # Apply settings
            self.apply_settings(settings)

            # Reload wallpapers if paths changed
            if paths_changed:
                self.status_label.set_text("Reloading wallpapers...")
                self.save_settings()  # Save paths immediately
                self.load_wallpapers()

        except Exception as e:
            self.log.error(f"Failed to apply settings: {e}")
        finally:
            dialog.destroy()  # Destroy dialog

    def apply_settings(self, settings):
        """Apply settings to current and future wallpapers."""

# Store settings
        self.settings = settings
        self.save_settings()  # Save settings to file

        # Update current wallpaper if running
        if self.engine.current_wallpaper:
            success, cmd = self.engine.run_wallpaper(
                self.engine.current_wallpaper,
                fps=settings["fps"],
                volume=settings["volume"],
                mute=settings["mute"],
                no_automute=settings["no_automute"],
                no_audio_processing=settings["no_audio_processing"],
                disable_mouse=settings["mouse_enabled"],
                no_fullscreen_pause=settings["no_fullscreen_pause"],
                scaling=settings["scaling"],
                clamping=settings["clamping"],
                enable_custom_args=settings["enable_custom_args"],
                custom_args=settings["custom_args"],
                enable_ld_preload=settings["enable_ld_preload"],
            )
            if success and cmd:
                self.update_command_status(cmd)

        # Handle auto-rotation
        if settings["auto_rotation"]:
            self.start_playlist_rotation(settings["rotation_interval"])
        else:
            self.stop_playlist_rotation()

    def start_playlist_rotation(self, interval):
        """Start automatic wallpaper rotation."""

if self.playlist_timeout:
            GLib.source_remove(self.playlist_timeout)

        def rotate_wallpaper():
            if wallpaper_id := self.engine.get_next_wallpaper():
                if self.engine.run_wallpaper(wallpaper_id):
                    self.update_current_wallpaper(wallpaper_id)
            return True

        # Convert minutes to milliseconds
        interval_ms = interval * 60 * 1000
        self.playlist_timeout = GLib.timeout_add(interval_ms, rotate_wallpaper)
        self.playlist_active = True

    def stop_playlist_rotation(self):
        """Stop automatic wallpaper rotation."""

if self.playlist_timeout:
            GLib.source_remove(self.playlist_timeout)
            self.playlist_timeout = None
        self.playlist_active = False

    def on_right_click(self, widget, event):
        """Handle right-click on wallpapers."""

if event.button == 3:  # Right click
            child = widget.get_child_at_pos(event.x, event.y)
            if child:
                wallpaper_id = child.get_child().wallpaper_id
                menu = WallpaperContextMenu(self, wallpaper_id)
                menu.popup_at_pointer(event)
                return True
        return False

    def on_destroy(self, window):
        """Clean up before exit."""

self.log.info("Shutting down...")
        # Don't stop wallpaper on exit - let it continue running
        Gtk.main_quit()

    def on_mute_toggled(self, button):
        """Handle mute button toggle."""

is_muted = button.get_active()

        # Update settings
        self.settings["mute"] = is_muted

        if is_muted:
            # Store current volume and set to 0
            self.last_volume = self.volume_scale.get_value()
            self.volume_scale.set_value(0)
            icon_name = "audio-volume-muted-symbolic"
        else:
            # Restore last volume
            self.volume_scale.set_value(self.last_volume)
            icon_name = "audio-volume-high-symbolic"

        self.volume_icon.set_from_icon_name(icon_name, Gtk.IconSize.SMALL_TOOLBAR)

        if self.engine.current_wallpaper:
            success, cmd = self._load_wallpaper(self.engine.current_wallpaper)
            if success and cmd:
                self.update_command_status(cmd)

    def on_volume_changed(self, scale):
        """Handle volume scale changes."""

volume = scale.get_value()

        # Update settings
        self.settings["volume"] = volume
        self.settings["mute"] = volume == 0

        # Update volume icon based on level
        if volume == 0:
            icon_name = "audio-volume-muted-symbolic"
            if not self.mute_button.get_active():
                self.mute_button.set_active(True)
        else:
            if volume < 33:
                icon_name = "audio-volume-low-symbolic"
            elif volume < 66:
                icon_name = "audio-volume-medium-symbolic"
            else:
                icon_name = "audio-volume-high-symbolic"
            if self.mute_button.get_active():
                self.mute_button.set_active(False)

        self.volume_icon.set_from_icon_name(icon_name, Gtk.IconSize.SMALL_TOOLBAR)

        if self.engine.current_wallpaper:
            success, cmd = self._load_wallpaper(self.engine.current_wallpaper)
            if success and cmd:
                self.update_command_status(cmd)

    def update_command_status(self, command):
        """Update status bar with last command."""

self.statusbar.pop(self.command_context)
        self.statusbar.push(self.command_context, f"Last command: {' '.join(map(str, command))}")

    def load_settings(self):
        """Load settings from config file."""

config_dir = os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
        config_file = os.path.join(config_dir, "settings.json")

        try:
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    saved_settings = json.load(f)
                    # Update defaults with saved settings
                    self.settings.update(saved_settings)

                    # Load engine paths if saved
                    if "wpe_path" in saved_settings and saved_settings["wpe_path"]:
                        self.engine.wpe_path = saved_settings["wpe_path"]
                        self.log.info(
                            f"Loaded saved wallpaper engine path: {saved_settings['wpe_path']}"
                        )

                    if "wallpaper_dir" in saved_settings and saved_settings["wallpaper_dir"]:
                        self.engine.wallpaper_dir = saved_settings["wallpaper_dir"]
                        self.log.info(
                            f"Loaded saved wallpaper directory: {saved_settings['wallpaper_dir']}"
                        )

                    self.log.debug(f"Loaded settings: {self.settings}")
        except Exception as e:
            self.log.error(f"Failed to load settings: {e}")

    def save_settings(self):
        """Save settings to config file."""

config_dir = os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
        config_file = os.path.join(config_dir, "settings.json")

        try:
            # Create config directory if it doesn't exist
            os.makedirs(config_dir, exist_ok=True)

            # Include engine paths in settings
            settings_to_save = self.settings.copy()
            settings_to_save["wpe_path"] = self.engine.wpe_path
            settings_to_save["wallpaper_dir"] = self.engine.wallpaper_dir

            with open(config_file, "w") as f:
                json.dump(settings_to_save, f, indent=4)
                self.log.debug(f"Saved settings with paths: {settings_to_save}")
        except Exception as e:
            self.log.error(f"Failed to save settings: {e}")

    def check_initial_setup(self):
        """Check if initial setup is needed."""
        # Check for Wayland first
        if self.engine._is_wayland():
            dialog = Gtk.MessageDialog(
                parent=self,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Wayland Session Detected!",
            )
            dialog.format_secondary_text(
                "⚠️ Linux Wallpaper Engine is NOT compatible with Wayland sessions.\n\n"
                "Wallpapers will not display properly or may not work at all.\n\n"
                "Please log out and select an X11/Xorg session instead.\n"
                "Look for options like 'Ubuntu on Xorg' or 'GNOME on Xorg' on your login screen."
            )
            dialog.run()
            dialog.destroy()

        if not self.engine.wpe_path or not self.engine.wallpaper_dir:
            self.log.info("Initial setup needed - opening settings dialog")

            # Show a helpful message
            dialog = Gtk.MessageDialog(
                parent=self,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Setup Required",
            )
            dialog.format_secondary_text(
                "Linux Wallpaper Engine GTK needs to be configured.\n\n"
                "Please specify:\n"
                "• Path to linux-wallpaperengine executable\n"
                "• Steam Workshop wallpaper directory\n\n"
                "The settings dialog will open to configure these paths."
            )
            dialog.run()
            dialog.destroy()

            # Open settings dialog
            self.on_setup_clicked(None)
        return False  # Don't repeat this idle callback
