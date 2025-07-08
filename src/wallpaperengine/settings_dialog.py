

import os

from gi.repository import Gtk


class SettingsDialog(Gtk.Dialog):
    """GTK dialog for managing application settings and configuration.

Provides a comprehensive settings interface with tabs for performance,
    audio, display, interaction, playlist, paths, and advanced options."""

    def __init__(self, parent):
        """Initialize the settings dialog.

Args:
            parent: The parent window to attach this dialog to."""
        super().__init__(title="Settings", parent=parent, flags=0)
        self.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK)

        self.parent = parent
        self.set_default_size(400, 500)

        # Load current settings
        self.current_settings = parent.settings

        # Create notebook for settings tabs
        notebook = Gtk.Notebook()
        box = self.get_content_area()
        box.add(notebook)

        # Performance settings
        perf_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(perf_grid, Gtk.Label(label="Performance"))

        # FPS settings
        fps_label = Gtk.Label(label="Default FPS:", halign=Gtk.Align.END)
        self.fps_spin = Gtk.SpinButton.new_with_range(1, 240, 1)
        self.fps_spin.set_value(self.current_settings["fps"])
        perf_grid.attach(fps_label, 0, 0, 1, 1)
        perf_grid.attach(self.fps_spin, 1, 0, 1, 1)

        # Audio settings
        audio_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(audio_grid, Gtk.Label(label="Audio"))

        # Audio switches
        switches = [
            (
                "Keep Playing When Other Apps Play Sound",
                "no_automute_switch",
                "no_automute",
                "By default, wallpaper audio is muted when other applications play sound. "
                + "Enable this to keep wallpaper audio playing.",
            ),
            (
                "Disable Audio Effects",
                "no_audio_processing_switch",
                "no_audio_processing",
                "Disables all audio post-processing effects that may be defined in the wallpaper. "
                + "Can improve performance or fix audio issues.",
            ),
        ]

        for i, (label, name, setting_key, tooltip) in enumerate(switches):
            label_widget = Gtk.Label(label=label + ":", halign=Gtk.Align.END)
            label_widget.set_line_wrap(True)  # Allow labels to wrap
            label_widget.set_max_width_chars(30)  # Limit width for better layout
            switch = Gtk.Switch()
            switch.set_tooltip_text(tooltip)
            switch.set_active(self.current_settings[setting_key])
            setattr(self, name, switch)
            audio_grid.attach(label_widget, 0, i + 1, 1, 1)
            audio_grid.attach(switch, 1, i + 1, 1, 1)

        # Display settings
        display_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(display_grid, Gtk.Label(label="Display"))

        # Scaling mode
        scale_label = Gtk.Label(label="Scaling Mode:", halign=Gtk.Align.END)
        self.scaling_combo = Gtk.ComboBoxText()
        for mode in ["default", "stretch", "fit", "fill"]:
            self.scaling_combo.append_text(mode)
        scaling_mode = self.current_settings.get("scaling", "default")
        self.scaling_combo.set_active(
            ["default", "stretch", "fit", "fill"].index(scaling_mode or "default")
        )
        display_grid.attach(scale_label, 0, 0, 1, 1)
        display_grid.attach(self.scaling_combo, 1, 0, 1, 1)

        # Clamping mode
        clamp_label = Gtk.Label(label="Clamping Mode:", halign=Gtk.Align.END)
        self.clamping_combo = Gtk.ComboBoxText()
        for mode in ["clamp", "border", "repeat"]:
            self.clamping_combo.append_text(mode)
        clamping_mode = self.current_settings.get("clamping", "clamp")
        self.clamping_combo.set_active(
            ["clamp", "border", "repeat"].index(clamping_mode or "clamp")
        )
        display_grid.attach(clamp_label, 0, 1, 1, 1)
        display_grid.attach(self.clamping_combo, 1, 1, 1, 1)

        # Add interaction settings after audio settings
        interact_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(interact_grid, Gtk.Label(label="Interaction"))

        # Mouse interaction
        self.mouse_switch = Gtk.Switch()
        self.mouse_switch.set_active(self.current_settings["mouse_enabled"])
        mouse_label = Gtk.Label(label="Disable Mouse Interaction:", halign=Gtk.Align.END)
        interact_grid.attach(mouse_label, 0, 0, 1, 1)
        interact_grid.attach(self.mouse_switch, 1, 0, 1, 1)

        # Fullscreen pause
        self.no_fullscreen_pause_switch = Gtk.Switch()
        self.no_fullscreen_pause_switch.set_active(self.current_settings["no_fullscreen_pause"])
        pause_label = Gtk.Label(label="Disable Fullscreen Pause:", halign=Gtk.Align.END)
        interact_grid.attach(pause_label, 0, 1, 1, 1)
        interact_grid.attach(self.no_fullscreen_pause_switch, 1, 1, 1, 1)

        # Add playlist settings after interaction settings
        playlist_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(playlist_grid, Gtk.Label(label="Playlist"))

        # Auto-rotation
        self.rotation_switch = Gtk.Switch()
        self.rotation_switch.set_active(self.current_settings["auto_rotation"])
        rotation_label = Gtk.Label(label="Enable Auto-rotation:", halign=Gtk.Align.END)
        playlist_grid.attach(rotation_label, 0, 0, 1, 1)
        playlist_grid.attach(self.rotation_switch, 1, 0, 1, 1)

        # Rotation interval
        interval_label = Gtk.Label(label="Rotation Interval (minutes):", halign=Gtk.Align.END)
        self.interval_spin = Gtk.SpinButton.new_with_range(1, 1440, 1)
        self.interval_spin.set_value(self.current_settings["rotation_interval"])
        playlist_grid.attach(interval_label, 0, 1, 1, 1)
        playlist_grid.attach(self.interval_spin, 1, 1, 1, 1)

        # Add paths configuration tab
        paths_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(paths_grid, Gtk.Label(label="Paths"))

        # Wallpaper Engine Path
        wpe_label = Gtk.Label(label="Wallpaper Engine Path:", halign=Gtk.Align.END)
        wpe_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.wpe_entry = Gtk.Entry()
        self.wpe_entry.set_text(parent.engine.wpe_path or "")
        self.wpe_entry.set_placeholder_text("Path to linux-wallpaperengine executable")
        wpe_browse_btn = Gtk.Button(label="Browse...")
        wpe_browse_btn.connect("clicked", self.on_browse_wpe_path)
        wpe_box.pack_start(self.wpe_entry, True, True, 0)
        wpe_box.pack_start(wpe_browse_btn, False, False, 0)
        paths_grid.attach(wpe_label, 0, 0, 1, 1)
        paths_grid.attach(wpe_box, 1, 0, 1, 1)

        # Wallpaper Directory Path
        wallpaper_label = Gtk.Label(label="Wallpaper Directory:", halign=Gtk.Align.END)
        wallpaper_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.wallpaper_entry = Gtk.Entry()
        self.wallpaper_entry.set_text(parent.engine.wallpaper_dir or "")
        self.wallpaper_entry.set_placeholder_text("Steam Workshop wallpaper directory")
        wallpaper_browse_btn = Gtk.Button(label="Browse...")
        wallpaper_browse_btn.connect("clicked", self.on_browse_wallpaper_dir)
        wallpaper_box.pack_start(self.wallpaper_entry, True, True, 0)
        wallpaper_box.pack_start(wallpaper_browse_btn, False, False, 0)
        paths_grid.attach(wallpaper_label, 0, 1, 1, 1)
        paths_grid.attach(wallpaper_box, 1, 1, 1, 1)

        # Help text
        help_label = Gtk.Label()
        help_label.set_markup(
            "<i>If paths are not detected automatically, use the Browse buttons to locate:\n"
            "• linux-wallpaperengine executable\n"
            "• Steam Workshop content directory (usually ~/.steam/steam/steamapps/"
            "workshop/content/431960)</i>"
        )
        help_label.set_line_wrap(True)
        help_label.set_max_width_chars(50)
        paths_grid.attach(help_label, 0, 2, 2, 1)

        # Add Advanced CEF Arguments tab (after paths configuration)
        advanced_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(advanced_grid, Gtk.Label(label="Advanced"))

        # Enable custom arguments
        self.custom_args_switch = Gtk.Switch()
        self.custom_args_switch.set_active(self.current_settings.get("enable_custom_args", False))
        custom_args_label = Gtk.Label(label="Enable Custom CEF Arguments:", halign=Gtk.Align.END)
        custom_args_label.set_tooltip_text(
            "Enable custom CEF arguments for compatibility fixes and advanced options"
        )
        advanced_grid.attach(custom_args_label, 0, 0, 1, 1)
        advanced_grid.attach(self.custom_args_switch, 1, 0, 1, 1)

        # Custom arguments entry
        args_label = Gtk.Label(label="Custom Arguments:", halign=Gtk.Align.END)
        self.custom_args_entry = Gtk.Entry()
        self.custom_args_entry.set_text(self.current_settings.get("custom_args", ""))
        self.custom_args_entry.set_placeholder_text("e.g., --no-sandbox --single-process")
        self.custom_args_entry.set_tooltip_text(
            "Additional command-line arguments for linux-wallpaperengine"
        )
        advanced_grid.attach(args_label, 0, 1, 1, 1)
        advanced_grid.attach(self.custom_args_entry, 1, 1, 1, 1)

        # Presets dropdown
        presets_label = Gtk.Label(label="Quick Presets:", halign=Gtk.Align.END)
        self.presets_combo = Gtk.ComboBoxText()
        self.presets_combo.append_text("Custom...")
        self.presets_combo.append_text("Intel Graphics Fix (CEF v119+)")
        self.presets_combo.append_text("Debug Mode")
        self.presets_combo.append_text("Performance Mode")
        self.presets_combo.set_active(0)
        self.presets_combo.connect("changed", self.on_preset_changed)
        advanced_grid.attach(presets_label, 0, 2, 1, 1)
        advanced_grid.attach(self.presets_combo, 1, 2, 1, 1)

        # LD_PRELOAD option
        self.ld_preload_switch = Gtk.Switch()
        self.ld_preload_switch.set_active(self.current_settings.get("enable_ld_preload", False))
        ld_preload_label = Gtk.Label(label="Enable LD_PRELOAD Fix:", halign=Gtk.Align.END)
        ld_preload_label.set_tooltip_text(
            "Preload libcef.so to fix CEF v119+ static TLS allocation issues"
        )
        advanced_grid.attach(ld_preload_label, 0, 3, 1, 1)
        advanced_grid.attach(self.ld_preload_switch, 1, 3, 1, 1)

        # Help text for advanced options
        advanced_help = Gtk.Label()
        advanced_help.set_markup(
            "<b>Advanced CEF Options Help:</b>\n\n"
            + "<b>Intel Graphics Fix:</b> Solves CEF v119+ crashes with "
            "--no-sandbox --single-process\n"
            + "<b>LD_PRELOAD Fix:</b> Fixes static TLS allocation issues on modern CEF versions\n"
            + "<b>Debug Mode:</b> Enables CEF debugging and verbose logging\n"
            + "<b>Performance Mode:</b> Optimizes for better performance on low-end systems\n\n"
            + "<i>⚠️ These options fix known compatibility issues but may affect stability</i>"
        )
        advanced_help.set_line_wrap(True)
        advanced_help.set_max_width_chars(60)
        advanced_help.set_halign(Gtk.Align.START)
        advanced_grid.attach(advanced_help, 0, 4, 2, 1)

        # Connect switch to enable/disable entry
        self.custom_args_switch.connect("notify::active", self.on_custom_args_toggled)

        # Initialize the UI state
        self.on_custom_args_toggled(self.custom_args_switch, None)

        self.show_all()

    def on_browse_wpe_path(self, button):
        """Browse for wallpaper engine executable."""
        dialog = Gtk.FileChooserDialog(
            title="Select linux-wallpaperengine executable",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        # Set initial directory
        if self.wpe_entry.get_text():
            dialog.set_filename(self.wpe_entry.get_text())
        else:
            dialog.set_current_folder(os.path.expanduser("~"))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.wpe_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def on_browse_wallpaper_dir(self, button):
        """Browse for wallpaper directory."""
        dialog = Gtk.FileChooserDialog(
            title="Select wallpaper directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        # Set initial directory
        if self.wallpaper_entry.get_text():
            dialog.set_current_folder(self.wallpaper_entry.get_text())
        else:
            # Try to find Steam directory
            for steam_path in [
                "~/.steam/steam/steamapps/workshop/content/431960",
                "~/.local/share/Steam/steamapps/workshop/content/431960",
            ]:
                expanded = os.path.expanduser(steam_path)
                if os.path.exists(expanded):
                    dialog.set_current_folder(expanded)
                    break
            else:
                dialog.set_current_folder(os.path.expanduser("~"))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.wallpaper_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def on_preset_changed(self, combo):
        """Handle selection of a preset from the advanced options combo box."""
        selected_preset = self.presets_combo.get_active_text()
        if selected_preset == "Intel Graphics Fix (CEF v119+)":
            self.custom_args_entry.set_text("--no-sandbox --single-process")
            self.ld_preload_switch.set_active(True)
        elif selected_preset == "Debug Mode":
            self.custom_args_entry.set_text("--debug-level=2")
            self.ld_preload_switch.set_active(False)
        elif selected_preset == "Performance Mode":
            self.custom_args_entry.set_text("--disable-gpu-vsync --disable-gpu-compositing")
            self.ld_preload_switch.set_active(False)
        elif selected_preset == "Custom...":
            self.custom_args_entry.set_text("")
            self.ld_preload_switch.set_active(False)

    def on_custom_args_toggled(self, switch, gparam):
        """Handle the custom arguments switch toggle."""
        is_active = switch.get_active()
        if is_active:
            self.custom_args_entry.set_sensitive(True)
            self.presets_combo.set_sensitive(True)
            self.ld_preload_switch.set_sensitive(True)
        else:
            self.custom_args_entry.set_sensitive(False)
            self.presets_combo.set_sensitive(False)
            self.ld_preload_switch.set_sensitive(False)
