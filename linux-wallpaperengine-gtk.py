#!/usr/bin/env python3
"""
Linux Wallpaper Engine GTK Frontend
A standalone GTK interface for linux-wallpaperengine
"""

# Standard library imports
import logging, os, json, sys, random, argparse, subprocess, threading, logging, time, shutil, datetime, pathlib, typing, gi
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any, Set, Union, Callable

# GTK imports
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk

"""

class SettingsDialog(Gtk.Dialog):

    def __init__(self, parent: WallpaperWindow):
        super().__init__(title="Settings", parent=parent, flags=0)
        notebook = Gtk.Notebook()
        box = self.get_content_area()
        box.add(notebook)
        
        # Performance settings
        perf_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(perf_grid, Gtk.Label(label="Performance"))
        
        # FPS settings
        fps_label = Gtk.Label(label="Default FPS:", halign=Gtk.Align.END)
        self.fps_spin = Gtk.SpinButton.new_with_range(1, 240, 1)
        self.fps_spin.set_value(self.current_settings['fps'])
        perf_grid.attach(fps_label, 0, 0, 1, 1)
        perf_grid.attach(self.fps_spin, 1, 0, 1, 1)
        
        # Audio settings
        audio_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(audio_grid, Gtk.Label(label="Audio"))
        
        # Audio switches
        switches = [
            ("Keep Playing When Other Apps Play Sound", "no_automute_switch", "no_automute", 
             "By default, wallpaper audio is muted when other applications play sound. " +
             "Enable this to keep wallpaper audio playing."),
            ("Disable Audio Effects", "no_audio_processing_switch", "no_audio_processing", 
             "Disables all audio post-processing effects that may be defined in the wallpaper. " +
             "Can improve performance or fix audio issues.")
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
        scaling_mode = self.current_settings.get('scaling', 'default')
        self.scaling_combo.set_active(["default", "stretch", "fit", "fill"].index(scaling_mode or 'default'))
        display_grid.attach(scale_label, 0, 0, 1, 1)
        display_grid.attach(self.scaling_combo, 1, 0, 1, 1)
        
        # Clamping mode
        clamp_label = Gtk.Label(label="Clamping Mode:", halign=Gtk.Align.END)
        self.clamping_combo = Gtk.ComboBoxText()
        for mode in ["clamp", "border", "repeat"]:
            self.clamping_combo.append_text(mode)
        clamping_mode = self.current_settings.get('clamping', 'clamp')
        self.clamping_combo.set_active(["clamp", "border", "repeat"].index(clamping_mode or 'clamp'))
        display_grid.attach(clamp_label, 0, 1, 1, 1)
        display_grid.attach(self.clamping_combo, 1, 1, 1, 1)
        
        # Add interaction settings after audio settings
        interact_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(interact_grid, Gtk.Label(label="Interaction"))
        
        # Mouse interaction
        self.mouse_switch = Gtk.Switch()
        self.mouse_switch.set_active(self.current_settings['mouse_enabled'])
        mouse_label = Gtk.Label(label="Disable Mouse Interaction:", halign=Gtk.Align.END)
        interact_grid.attach(mouse_label, 0, 0, 1, 1)
        interact_grid.attach(self.mouse_switch, 1, 0, 1, 1)
        
        # Fullscreen pause
        self.no_fullscreen_pause_switch = Gtk.Switch()
        self.no_fullscreen_pause_switch.set_active(self.current_settings['no_fullscreen_pause'])
        pause_label = Gtk.Label(label="Disable Fullscreen Pause:", halign=Gtk.Align.END)
        interact_grid.attach(pause_label, 0, 1, 1, 1)
        interact_grid.attach(self.no_fullscreen_pause_switch, 1, 1, 1, 1)
        
        # Add playlist settings after interaction settings
        playlist_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(playlist_grid, Gtk.Label(label="Playlist"))
        
        # Auto-rotation
        self.rotation_switch = Gtk.Switch()
        self.rotation_switch.set_active(self.current_settings['auto_rotation'])
        rotation_label = Gtk.Label(label="Enable Auto-rotation:", halign=Gtk.Align.END)
        playlist_grid.attach(rotation_label, 0, 0, 1, 1)
        playlist_grid.attach(self.rotation_switch, 1, 0, 1, 1)
        
        # Rotation interval
        interval_label = Gtk.Label(label="Rotation Interval (minutes):", halign=Gtk.Align.END)
        self.interval_spin = Gtk.SpinButton.new_with_range(1, 1440, 1)
        self.interval_spin.set_value(self.current_settings['rotation_interval'])
        playlist_grid.attach(interval_label, 0, 1, 1, 1)
        playlist_grid.attach(self.interval_spin, 1, 1, 1, 1)
        
        self.show_all()

class WallpaperContextMenu(Gtk.Menu):
    def __init__(self, parent, wallpaper_id):
        super().__init__()
        self.parent = parent
        self.wallpaper_id = wallpaper_id
        
        # Apply wallpaper
        apply_item = Gtk.MenuItem(label="Apply Wallpaper")
        apply_item.connect("activate", self.on_apply_clicked)
        self.append(apply_item)
        
        # Add to playlist
        playlist_item = Gtk.MenuItem(label="Add to Playlist")
        playlist_item.connect("activate", self.on_playlist_clicked)
        self.append(playlist_item)
        
        self.show_all()
    
    def on_apply_clicked(self, widget):
        if self.parent.engine.run_wallpaper(self.wallpaper_id):
            self.parent.update_current_wallpaper(self.wallpaper_id)
    
    def on_playlist_clicked(self, widget):
        # TODO: Implement playlist management
        pass

#the above should be picked for remaining functions to integrate into settings!!!

TODO: Major Feature Areas

1. Testing Infrastructure
------------------------
- Test Directory Structure
  * tests/__init__.py
  * tests/conftest.py (shared fixtures)
  * tests/test_wallpaperengine.py
  * tests/test_directory_manager.py
  * tests/test_resource_monitor.py
  * tests/test_ui.py

- Core Engine Tests
  * WPE path detection scenarios
  * Display detection with mocks
  * Process management lifecycle
  * Wallpaper switching reliability
  * Error handling coverage
  * State management verification

- Directory Management Tests
  * Steam library detection
  * Workshop content scanning
  * Path validation
  * Auto-refresh functionality
  * Multiple directory handling
  * Permission scenarios

- Resource Monitoring Tests
  * CPU usage tracking accuracy
  * Memory usage monitoring
  * GPU utilization detection
  * Power consumption tracking
  * Resource limit enforcement
  * Long-running stability

- UI Testing
  * Preview loading performance
  * Settings dialog validation
  * Keyboard shortcut handling
  * Widget lifecycle management
  * Event handling coverage
  * Memory leak detection

2. System Stability & Robustness
------------------------------
- Display manager event handling
  * Session suspend/resume
  * Display hotplug
  * Resolution changes
  * Multi-monitor reconfiguration
  * Compositor crashes/restarts
  * X11/Wayland session changes

- Process Management
  * Graceful process termination
  * Zombie process prevention
  * Process cleanup on crashes
  * Resource cleanup on exit
  * IPC error handling
  * Signal handling (SIGTERM, SIGINT, etc.)

- State Recovery
  * Automatic crash recovery
  * Session state persistence
  * Configuration backup
  * Wallpaper process monitoring
  * Auto-restart on failure
  * State verification

3. Error Detection & Debugging
------------------------------
- Path Validation
  * Edge case detection
  * Permission handling
  * Invalid path scenarios
  * Network path handling
  * Symlink resolution
  * Path normalization

- Process Management
  * Zombie process prevention
  * Orphaned process cleanup
  * Signal handling coverage
  * IPC error detection
  * Resource cleanup verification
  * State recovery procedures

- Memory Management
  * Leak detection tools
  * Resource tracking
  * Widget cleanup
  * Buffer management
  * Cache optimization
  * GC triggering

- Performance Profiling
  * CPU hotspot detection
  * Memory usage patterns
  * I/O bottleneck analysis
  * UI responsiveness metrics
  * Resource usage trending
  * Optimization opportunities

4. Directory Management
----------------------
- WallpaperDirectoryManager class for handling multiple wallpaper sources
- Support for multiple Steam library locations
- Custom wallpaper directories
- Auto-detection of Steam libraries
- Workshop ID configuration (431960 default)
- Directory enable/disable toggles
- Directory scan depth configuration
- Directory auto-refresh settings

5. Performance Considerations
---------------------------
- CPU/GPU usage monitoring
- Memory usage tracking
- Power consumption profiles
- Auto-adjustment based on battery
- Process priority management
- Resource usage limits
- Performance logging
- Auto-optimization features

6. Resource Management
--------------------
- Memory leak prevention
- Resource limit enforcement
- Buffer cleanup
- Image cache management
- GObject/GTK cleanup
- Pixbuf memory handling
- Preview caching system
- Auto-cleanup features

7. Error Handling
---------------
- Comprehensive error logging
- User-friendly error messages
- Recovery procedures
- Diagnostic tools
- Debug mode
- Error reporting
- Auto-recovery features
- State preservation
- Filesystem error handling
- Network timeout handling
- IPC error recovery
- X11 error trapping
- GTK warning suppression
- Exception boundary definition

8. Enhanced Settings Management
-----------------------------
- Advanced settings dialog with multiple tabs
- Directory management UI
- Performance profiles
- Custom command-line arguments
- Configuration import/export
- Default settings templates
- Settings backup/restore

9. Mobile Device Support
----------------------
- Battery-aware performance modes
- Reduced animation mode
- Touch-friendly UI layout
- Screen rotation handling
- Bandwidth-conscious preview loading
- Memory usage optimization
- Power consumption monitoring
- Mobile-specific UI scaling

10. UI Enhancements
----------------
- Mobile-friendly controls
- Touch gesture support
- Adaptive layout system
- UI scale factors
- High-DPI support
- Accessibility features
- Keyboard navigation
- Screen reader support

12. Advanced Features
------------------
- Multiple monitor support
- Per-monitor settings
- Wallpaper playlists
- Auto-switching rules
- Event-based triggers
- Time-based scheduling
- Tag-based organization
- Search and filtering

13. System Integration
-------------------
- Session management
- Startup integration
- System tray support
- Desktop environment detection
- Multi-user support
- Permission management
- System event handling
- Service integration

14. Plugin System
----------------
- Theme support
- Language localization
- Remote control
- Cloud integration
- Update system
- Backup/restore
- Migration tools
"""
class UIHelper:
    """Helper class for creating common GTK UI components."""

    @staticmethod
    def add_spin_button(container: Gtk.Container, label: str, min_value: int, max_value: int, initial_value: int, row: int) -> Gtk.SpinButton:
        """Create and add a spin button to the container."""
        adjustment = Gtk.Adjustment(value=initial_value, lower=min_value, upper=max_value, step_increment=1)
        spin_button = Gtk.SpinButton(adjustment=adjustment)
        if isinstance(container, Gtk.Grid):
            container.attach(Gtk.Label(label=label), 0, row, 1, 1)
            container.attach(spin_button, 1, row, 1, 1)
        elif isinstance(container, Gtk.Box):
            container.pack_start(Gtk.Label(label=label), False, False, 0)
            container.pack_start(spin_button, False, False, 0)
        return spin_button

    @staticmethod
    def add_scale(container: Gtk.Container, label: str, min_value: int, max_value: int, initial_value: int, row: int) -> Gtk.Scale:
        """Create and add a scale to the container."""
        adjustment = Gtk.Adjustment(value=initial_value, lower=min_value, upper=max_value, step_increment=1)
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        if isinstance(container, Gtk.Grid):
            container.attach(Gtk.Label(label=label), 0, row, 1, 1)
            container.attach(scale, 1, row, 1, 1)
        elif isinstance(container, Gtk.Box):
            container.pack_start(Gtk.Label(label=label), False, False, 0)
            container.pack_start(scale, False, False, 0)
        return scale

    @staticmethod
    def add_switch(container: Gtk.Container, label: str, initial_value: bool, row: int) -> Gtk.Switch:
        """Create and add a switch to the container."""
        switch = Gtk.Switch()
        switch.set_active(initial_value)
        if isinstance(container, Gtk.Grid):
            container.attach(Gtk.Label(label=label), 0, row, 1, 1)
            container.attach(switch, 1, row, 1, 1)
        elif isinstance(container, Gtk.Box):
            container.pack_start(Gtk.Label(label=label), False, False, 0)
            container.pack_start(switch, False, False, 0)
        return switch

    @staticmethod
    def add_combo_box(container: Gtk.Container, label: str, options: list, initial_value: str, row: int) -> Gtk.ComboBoxText:
        """Create and add a combo box to the container."""
        combo_box = Gtk.ComboBoxText()
        for option in options:
            combo_box.append_text(option)
        combo_box.set_active(options.index(initial_value) if initial_value in options else 0)
        if isinstance(container, Gtk.Grid):
            container.attach(Gtk.Label(label=label), 0, row, 1, 1)
            container.attach(combo_box, 1, row, 1, 1)
        elif isinstance(container, Gtk.Box):
            container.pack_start(Gtk.Label(label=label), False, False, 0)
            container.pack_start(combo_box, False, False, 0)
        return combo_box

class WelcomeDialog(Gtk.Dialog):

    """Welcome dialog for first-time setup."""
    
    def __init__(self, parent=None):
        super().__init__(
            title="Welcome to Linux Wallpaper Engine",
            parent=parent,
            flags=0
        )
        self.set_default_size(600, 400)
        
        # Add buttons
        self.add_buttons(
            "Exit", Gtk.ResponseType.CANCEL,
            "Continue", Gtk.ResponseType.OK
        )
        
        # Main content box
        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        # Welcome text
        welcome_label = Gtk.Label()
        welcome_label.set_markup(
            "<span size='x-large' weight='bold'>Welcome to Linux Wallpaper Engine!</span>\n\n"
            "This application requires linux-wallpaperengine to be installed.\n"
            "Please follow these steps to get started:"
        )
        welcome_label.set_line_wrap(True)
        welcome_label.set_justify(Gtk.Justification.CENTER)
        box.pack_start(welcome_label, False, False, 10)
        
        # Installation instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<b>Installation Steps:</b>\n\n"
            "1. Clone the repository:\n"
            "   <tt>git clone https://github.com/Almamu/linux-wallpaperengine</tt>\n\n"
            "2. Build the application:\n"
            "   <tt>cd linux-wallpaperengine\n"
            "   mkdir build &amp;&amp; cd build\n"
            "   cmake ..\n"
            "   make</tt>\n\n"
            "For more details, visit:\n"
            "<a href='https://github.com/Almamu/linux-wallpaperengine'>https://github.com/Almamu/linux-wallpaperengine</a>"
        )
        instructions.set_line_wrap(True)
        instructions.set_justify(Gtk.Justification.LEFT)
        instructions.set_selectable(True)
        box.pack_start(instructions, False, False, 10)
        
        # Path selection
        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        path_label = Gtk.Label(label="WPE Path:")
        self.path_entry = Gtk.Entry()
        self.path_entry.set_placeholder_text("Path to linux-wallpaperengine executable")
        browse_button = Gtk.Button(label="Browse")
        browse_button.connect("clicked", self.on_browse_build_clicked)
        
        path_box.pack_start(path_label, False, False, 0)
        path_box.pack_start(self.path_entry, True, True, 0)
        path_box.pack_start(browse_button, False, False, 0)
        box.pack_start(path_box, False, False, 10)
        
        # Auto-detect button
        detect_button = Gtk.Button(label="Auto-detect")
        detect_button.connect("clicked", self.on_detect_clicked)
        box.pack_start(detect_button, False, False, 0)
        
        self.show_all()
    
    def on_browse_build_clicked(self, button):
        """Handle browse button click."""
        dialog = Gtk.FileChooserDialog(
            title="Select linux-wallpaperengine Executable",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.path_entry.set_text(dialog.get_filename())
        dialog.destroy()
    
    def on_detect_clicked(self, button):
        """Try to auto-detect WPE executable."""
        # Common base directories
        base_dirs = [
            "~",                    # Home directory
            "~/src",               # Common source directory
            "~/code",              # Common code directory
            "~/projects",          # Common projects directory
            "~/git",               # Common git directory
            "~/cursor",            # Cursor editor directory
            "~/Documents",         # Documents directory
            "~/workspace",         # Workspace directory
            "~/dev",               # Development directory
            os.path.expanduser("~")  # Full home directory for subdirectory search
        ]
        
        # Common repository names
        repo_names = [
            "linux-wallpaperengine",
            "wallpaperengine",
            "l-wpe",
            "wpe"
        ]
        
        # System paths
        system_paths = [
            "/usr/local/bin/linux-wallpaperengine",
            "/usr/bin/linux-wallpaperengine",
            os.path.expanduser("~/bin/linux-wallpaperengine")
        ]
        
        # Collect all possible paths
        possible_paths = []
        
        # Add system paths
        possible_paths.extend(system_paths)
        
        # Check PATH environment
        if path := shutil.which('linux-wallpaperengine'):
            possible_paths.append(path)
        
        # Search in base directories
        for base in base_dirs:
            base = os.path.expanduser(base)
            if not os.path.exists(base):
                continue
            
            # Direct repository locations
            for repo in repo_names:
                # Check build directory
                build_paths = [
                    os.path.join(base, repo, "build", "linux-wallpaperengine"),
                    os.path.join(base, repo, "build", repo),
                    os.path.join(base, repo, "bin", "linux-wallpaperengine"),
                    os.path.join(base, repo, "target", "linux-wallpaperengine")
                ]
                possible_paths.extend(build_paths)
            
            # Search one level deep for repository directories
            try:
                for entry in os.scandir(base):
                    if entry.is_dir():
                        for repo in repo_names:
                            if repo in entry.name.lower():
                                # Check build directory
                                build_paths = [
                                    os.path.join(entry.path, "build", "linux-wallpaperengine"),
                                    os.path.join(entry.path, "build", repo),
                                    os.path.join(entry.path, "bin", "linux-wallpaperengine"),
                                    os.path.join(entry.path, "target", "linux-wallpaperengine")
                                ]
                                possible_paths.extend(build_paths)
            except (PermissionError, OSError):
                continue
        
        # Try each path
        found_paths = []
        for path in possible_paths:
            try:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    found_paths.append(path)
            except Exception:
                continue
        
        if found_paths:
            # If multiple paths found, prefer local builds over system installations
            local_builds = [p for p in found_paths if "/usr/" not in p]
            if local_builds:
                self.path_entry.set_text(local_builds[0])
                return
            
            # Fall back to first found path
            self.path_entry.set_text(found_paths[0])
            return
        
        # Show error if not found
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Could not find linux-wallpaperengine"
        )
        dialog.format_secondary_text(
            "Please build and install linux-wallpaperengine first, "
            "or manually specify its location.\n\n"
            "Searched in common locations including:\n"
            "- Local build directories\n"
            "- System paths\n"
            "- Development directories"
        )
        dialog.run()
        dialog.destroy()

class WallpaperEngine:
    """Core wallpaper engine functionality"""
    
    def __init__(self, wpe_path=None):
        """Initialize wallpaper engine."""
        self.log = logging.getLogger('WallpaperEngine')
        self.display = self._detect_display()
        self.wpe_path = wpe_path if wpe_path else self._find_wpe_path()
        self.wallpaper_dir = self._find_wallpaper_dir()
        self.current_wallpaper = None
        self.current_process = None  # Track current wallpaper process
        
    def _detect_display(self):
        """Detect primary display using xrandr"""
        try:
            # Try primary display first
            result = subprocess.run("xrandr | grep -w 'primary'", 
                                  shell=True, capture_output=True, text=True)
            if result.stdout:
                display = result.stdout.split()[0]
                self.log.info(f"Found primary display: {display}")
                return display
                
            # Fall back to first connected display
            result = subprocess.run("xrandr | grep -w 'connected'", 
                                  shell=True, capture_output=True, text=True)
            if result.stdout:
                display = result.stdout.split()[0]
                self.log.info(f"Using display: {display}")
                return display
                
        except Exception as e:
            self.log.error(f"Display detection failed: {e}")
        return None
        
    def _find_wpe_path(self):
        """Find linux-wallpaperengine executable"""
        common_paths = [
            "~/linux-wallpaperengine/build/linux-wallpaperengine",
            "~/src/linux-wallpaperengine/build/linux-wallpaperengine",
            "/usr/local/bin/linux-wallpaperengine",
            "/usr/bin/linux-wallpaperengine",  # Add system-wide installation path
            os.path.expanduser("~/bin/linux-wallpaperengine"),  # Add user's bin directory
        ]
        
        for path in common_paths:
            full_path = os.path.expanduser(path)
            if os.path.isfile(full_path):
                self.log.info(f"Found WPE at: {full_path}")
                return full_path
        return None
        
    def _find_wallpaper_dir(self):
        """Find Steam Workshop wallpaper directory"""
        common_paths = [
            "~/.steam/steam/steamapps/workshop/content/431960",
            "~/.steam/debian-installation/steamapps/workshop/content/431960",
            "~/.local/share/Steam/steamapps/workshop/content/431960"
        ]
        
        for path in common_paths:
            full_path = os.path.expanduser(path)
            if os.path.isdir(full_path):
                self.log.info(f"Found wallpapers at: {full_path}")
                return full_path
        return None
        
    def get_wallpaper_list(self):
        """Get list of available wallpaper IDs"""
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
        """Select a random wallpaper ID"""
        wallpapers = self.get_wallpaper_list()
        if wallpapers:
            return random.choice(wallpapers)
        return None
        
    def get_next_wallpaper(self, current_id=None):
        """Get next wallpaper ID in sequence"""
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
        """Get previous wallpaper ID in sequence"""
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
            return wallpapers[-1]

    def run_wallpaper(self, wallpaper_id, **options):
        """Run wallpaper with specified options"""
        if not all([self.wpe_path, self.display, wallpaper_id]):
            self.log.error(f"Missing components - path: {self.wpe_path}, display: {self.display}, id: {wallpaper_id}")
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
            if options.get('fps'):
                cmd.extend(['--fps', str(options['fps'])])
            if options.get('mute'):
                cmd.append('--silent')
            if 'volume' in options:
                cmd.extend(['--volume', str(int(options['volume']))])
            if options.get('no_automute'):
                cmd.append('--noautomute')
            if options.get('no_audio_processing'):
                cmd.append('--no-audio-processing')
            if options.get('no_fullscreen_pause'):
                cmd.append('--no-fullscreen-pause')
            if options.get('disable_mouse'):
                cmd.append('--disable-mouse')
            if options.get('scaling'):
                cmd.extend(['--scaling', options['scaling']])
            if options.get('clamping'):
                cmd.extend(['--clamping', options['clamping']])
            
            # Add display and wallpaper ID
            cmd.extend(['--screen-root', self.display, wallpaper_id])
            
            self.log.info(f"Running command: {' '.join(map(str, cmd))}")
            
            # Create new process with stable configuration
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
                cwd=wpe_dir
            )
            
            # Brief pause to check if process started
            time.sleep(0.1)
            
            if process.poll() is None:  # Process is running
                self.current_wallpaper = wallpaper_id
                self.current_process = process
                self.log.info(f"Wallpaper process started successfully (PID: {process.pid})")
                return True, cmd
            else:
                self.log.error("Process failed to start")
                return False, None
            
        except Exception as e:
            self.log.error(f"Failed to run wallpaper: {str(e)}", exc_info=True)
            return False, None
            
        finally:
            self.log.debug(f"Returning to original directory: {original_dir}")
            os.chdir(original_dir)

    def stop_wallpaper(self):
        """Stop currently running wallpaper"""
        try:
            self.log.info("Stopping any running wallpaper processes...")
            
            # Keep trying until no processes remain
            while True:
                result = subprocess.run(['pgrep', '-f', f'{self.wpe_path}\\b'], 
                                      capture_output=True, text=True)
                self.log.debug(f"pgrep return code: {result.returncode}")
                if result.returncode != 0:  # No processes found
                    self.log.debug("No wallpaper processes found")
                    break
                    
                pids = result.stdout.strip().split('\n')
                self.log.debug(f"Found wallpaper processes: {pids}")
                
                # Try SIGTERM first
                self.log.debug("Sending SIGTERM to all processes")
                subprocess.run(['pkill', '-15', '-f', f'{self.wpe_path}\\b'])
                time.sleep(0.1)  # Brief pause
                
                # If processes still exist, use SIGKILL
                check = subprocess.run(['pgrep', '-f', f'{self.wpe_path}\\b'], 
                                     capture_output=True)
                self.log.debug(f"After SIGTERM check return code: {check.returncode}")
                if check.returncode == 0:
                    self.log.debug("SIGTERM failed, using SIGKILL")
                    subprocess.run(['pkill', '-9', '-f', f'{self.wpe_path}\\b'])
                    self.log.debug("Sent SIGKILL")
                    time.sleep(0.1)
                
                # Verify cleanup
                final_check = subprocess.run(['pgrep', '-f', f'{self.wpe_path}\\b'],
                                           capture_output=True)
                self.log.debug(f"Final check return code: {final_check.returncode}")
            
            self.current_process = None
            self.current_wallpaper = None
            self.log.info("All wallpaper processes stopped")
            time.sleep(0.2)  # Final pause before allowing new wallpaper
            return True

        except Exception as e:
            self.log.error(f"Failed to stop wallpaper: {e}", exc_info=True)
            return False

class WallpaperWindow(Gtk.Window):
    def __init__(self, wpe_path=None, initial_settings=None):
        super().__init__(title="Linux Wallpaper Engine")
        self.set_default_size(800, 600)
        
        # Initialize directory manager
        self.directory_manager = WallpaperDirectoryManager()  # Ensure this class is defined

        # Initialize engine with WPE path
        self.engine = WallpaperEngine(wpe_path)      
        # Setup logging
        self.log = logging.getLogger('GUI')
        
        # Preview size (default 200x120)
        self.preview_width = 200
        self.preview_height = 120
        
        # Playlist support
        self.playlist_timeout = None
        self.playlist_active = False
        
        # Default settings
        self.settings = {
            'fps': 60,
            'volume': 100,
            'mute': False,
            'mouse_enabled': True,
            'auto_rotation': False,
            'rotation_interval': 15,
            'no_automute': False,
            'no_audio_processing': False,
            'no_fullscreen_pause': False,
            'scaling': 'default',
            'clamping': 'clamp'
        }
        
        # Merge initial settings with defaults
        if initial_settings:
            self.settings.update(initial_settings)
        
        # Initialize UI
        self._setup_ui()
        
        # Load wallpapers
        self.load_wallpapers()
        
        self.connect("destroy", self.on_destroy)
        
        # Add CSS provider for styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .current-wallpaper {
                border: 3px solid @selected_bg_color;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Add runtime debugging helpers
        self._validate_state()
        self._verify_paths()
        
        # Validate critical components
        if not self._validate_state():
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="System State Invalid"
            )
            dialog.format_secondary_text(
                "Could not find required components.\n"
                "Please ensure linux-wallpaperengine is installed and accessible."
            )
            dialog.run()
            dialog.destroy()
            raise RuntimeError("Failed to initialize: Invalid system state")
        
        if not self._verify_paths():
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Required Paths Missing"
            )
            dialog.format_secondary_text(
                "Could not find required files or directories.\n"
                "Please check the application log for details."
            )
            dialog.run()
            dialog.destroy()
            raise RuntimeError("Failed to initialize: Missing required paths")

    def _setup_ui(self):
        """Setup main UI components"""
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
        """Create the toolbar with controls"""
        toolbar = Gtk.Toolbar()
        toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        
        # Status and volume controls container
        status_item = Gtk.ToolItem()
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Status label
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_halign(Gtk.Align.START)  # Modern left alignment
        self.status_label.set_valign(Gtk.Align.CENTER)  # Modern vertical center
        status_box.pack_start(self.status_label, True, True, 0)
        
        # Volume controls
        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Volume slider
        self.last_volume = 100  # Store last volume before mute
        adjustment = Gtk.Adjustment(
            value=100,
            lower=0,
            upper=100,
            step_increment=1,
            page_increment=10,
            page_size=0
        )
        self.volume_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        self.volume_scale.set_size_request(100, -1)
        self.volume_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.volume_scale.set_digits(0)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        vol_box.pack_start(self.volume_scale, False, False, 0)
        
        status_box.pack_start(vol_box, False, False, 6)
        status_item.add(status_box)
        status_item.set_expand(True)
        toolbar.insert(status_item, -1)
        
        # Preview size scale
        scale_item = Gtk.ToolItem()
        scale_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        scale_box.pack_start(Gtk.Label(label="Preview Size:"), False, False, 0)
        
        adjustment = Gtk.Adjustment(
            value=100,           # Default value (100%)
            lower=50,            # Minimum 50%
            upper=200,           # Maximum 200%
            step_increment=10,   # Small step
            page_increment=25,   # Large step
            page_size=0         # Required for scales
        )
        
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        scale.set_size_request(100, -1)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.set_digits(0)
        scale.connect("value-changed", self.on_preview_scale_changed)
        scale_box.pack_start(scale, True, True, 0)
        
        scale_item.add(scale_box)
        toolbar.insert(scale_item, -1)
        
        # Control buttons
        buttons = [
            ("media-skip-backward-symbolic", "Previous", self.on_prev_clicked),
            ("media-skip-forward-symbolic", "Next", self.on_next_clicked),
            ("media-playlist-shuffle-symbolic", "Random", self.on_random_clicked),
            ("preferences-system-symbolic", "Settings", self.on_settings_clicked)
        ]
        
        for icon_name, tooltip, callback in buttons:
            button = Gtk.ToolButton()
            button.set_icon_name(icon_name)
            button.set_tooltip_text(tooltip)
            button.connect("clicked", callback)
            toolbar.insert(button, -1)
        
        self.main_box.pack_start(toolbar, False, False, 0)

    def on_preview_scale_changed(self, scale):
        """Handle preview size scale changes"""
        percentage = scale.get_value() / 100.0
        self.preview_width = int(200 * percentage)   # Base width * scale
        self.preview_height = int(120 * percentage)  # Base height * scale
        self.reload_wallpapers()

    def load_wallpapers(self) -> None:
        """Load and display wallpaper previews.
        
        Handles loading and scaling of preview images, including GIF animations.
        Runs in background threads to prevent UI freezing.
        """
        def load_preview(wallpaper_id: str) -> None:
            preview_path: Optional[str] = None
            
            # Search for preview in all enabled directories
            for directory in self.directory_manager.get_enabled_directories():
                wallpaper_path = Path(directory) / wallpaper_id
                
                # Look for preview image
                for ext in ['.gif', '.png', '.jpg', '.webp', '.jpeg']:
                    path = wallpaper_path / f'preview{ext}'
                    if path.exists():
                        preview_path = str(path)
                        break
                if preview_path:
                    break
            
            if preview_path:
                try:
                    def add_preview() -> None:
                        box = Gtk.Box()
                        box.set_margin_start(2)
                        box.set_margin_end(2)
                        box.set_margin_top(2)
                        box.set_margin_bottom(2)
                        
                        try:
                            if preview_path.lower().endswith('.gif'):
                                self._handle_gif_preview(preview_path, box)
                            else:
                                self._handle_static_preview(preview_path, box)
                            
                            box.wallpaper_id = wallpaper_id
                            self.flowbox.add(box)
                            box.show_all()
                            
                            if wallpaper_id == self.engine.current_wallpaper:
                                self.highlight_current_wallpaper(box)
                            
                        except Exception as e:
                            self.log.error(f"Failed to create preview for {wallpaper_id}: {e}")
                    
                    GLib.idle_add(add_preview)
                    
                except Exception as e:
                    self.log.error(f"Failed to load preview for {wallpaper_id}: {e}")

        # Clear existing previews
        self.flowbox.foreach(lambda w: w.destroy())
        
        # Get wallpapers from all enabled directories
        wallpapers = self.directory_manager.get_all_wallpapers()
        self.status_label.set_text(f"Loading {len(wallpapers)} wallpapers...")
        
        for wallpaper_id in wallpapers:
            thread = threading.Thread(target=load_preview, args=(wallpaper_id,))
            thread.daemon = True
            thread.start()

    def _handle_gif_preview(self, preview_path: str, box: Gtk.Box) -> None:
        """Handle loading and displaying of GIF preview images.
        
        Args:
            preview_path: Path to the GIF file
            box: Container widget for the preview
        """
        animation = GdkPixbuf.PixbufAnimation.new_from_file(preview_path)
        
        if animation.is_static_image():
            pixbuf = animation.get_static_image().scale_simple(
                self.preview_width,
                self.preview_height,
                GdkPixbuf.InterpType.BILINEAR
            )
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            box.add(image)
            return
        
        # Handle animated GIF
        iter = animation.get_iter(None)
        first_frame = iter.get_pixbuf()
        scale_x = self.preview_width / first_frame.get_width()
        scale_y = self.preview_height / first_frame.get_height()
        scale = min(scale_x, scale_y)
        
        frames = []
        while True:
            pixbuf = iter.get_pixbuf()
            new_width = int(pixbuf.get_width() * scale)
            new_height = int(pixbuf.get_height() * scale)
            scaled_frame = pixbuf.scale_simple(
                new_width,
                new_height,
                GdkPixbuf.InterpType.BILINEAR
            )
            frames.append(scaled_frame)
            if not iter.advance():
                break
        
        image = Gtk.Image()
        box.add(image)
        
        def update_frame() -> bool:
            nonlocal frames
            current_frame = getattr(update_frame, 'current_frame', 0)
            image.set_from_pixbuf(frames[current_frame])
            update_frame.current_frame = (current_frame + 1) % len(frames)
            return True
        
        update_frame.current_frame = 0
        GLib.timeout_add(50, update_frame)

    def _handle_static_preview(self, preview_path: str, box: Gtk.Box) -> None:
        """Handle loading and displaying of static preview images.
        
        Args:
            preview_path: Path to the image file
            box: Container widget for the preview
        """
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            preview_path,
            self.preview_width,
            self.preview_height,
            True
        )
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        box.add(image)

    def reload_wallpapers(self):
        """Reload wallpapers with current preview size"""
        self.load_wallpapers()

    def highlight_current_wallpaper(self, current_box=None):
        """Update the highlight for the current wallpaper"""
        # Remove highlight from all boxes
        for child in self.flowbox.get_children():
            box = child.get_child()
            box.get_style_context().remove_class('current-wallpaper')
        
        # Add highlight to current box
        if current_box:
            current_box.get_style_context().add_class('current-wallpaper')

    def update_current_wallpaper(self, wallpaper_id):
        """Update UI to reflect current wallpaper"""
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
        """Handle wallpaper selection with validation."""
        if not self._validate_state():
            self.status_label.set_text("System state invalid")
            return
        
        if not self._verify_paths():
            self.status_label.set_text("Required paths missing")
            return
        
        if not self._check_permissions():
            self.status_label.set_text("Permission check failed")
            return
        
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
        """Load wallpaper with current settings"""
        return self.engine.run_wallpaper(
            wallpaper_id,
            fps=self.settings['fps'],
            volume=self.settings['volume'],
            mute=self.settings['mute'],
            no_automute=self.settings['no_automute'],
            no_audio_processing=self.settings['no_audio_processing'],
            disable_mouse=self.settings['mouse_enabled'],
            no_fullscreen_pause=self.settings['no_fullscreen_pause'],
            scaling=self.settings['scaling'],
            clamping=self.settings['clamping']
        )

    def on_prev_clicked(self, button):
        """Load previous wallpaper"""
        if wallpaper_id := self.engine.get_previous_wallpaper():
            success, cmd = self._load_wallpaper(wallpaper_id)
            if success:
                self.update_current_wallpaper(wallpaper_id)
                if cmd:
                    self.update_command_status(cmd)

    def on_next_clicked(self, button):
        """Load next wallpaper"""
        if wallpaper_id := self.engine.get_next_wallpaper():
            success, cmd = self._load_wallpaper(wallpaper_id)
            if success:
                self.update_current_wallpaper(wallpaper_id)
                if cmd:
                    self.update_command_status(cmd)

    def on_random_clicked(self, button):
        """Load random wallpaper"""
        if wallpaper_id := self.engine.get_random_wallpaper():
            success, cmd = self._load_wallpaper(wallpaper_id)
            if success:
                self.update_current_wallpaper(wallpaper_id)
                if cmd:
                    self.update_command_status(cmd)

    def on_settings_clicked(self, button: Optional[Gtk.Button] = None) -> None:
        """Open settings dialog."""
        dialog = SettingsDialog(self, self.settings)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Reload wallpapers if directories have changed
            self.load_wallpapers()
        
        dialog.destroy()

    def on_right_click(self, widget: Gtk.Widget, event: Gdk.EventButton) -> bool:
        """Handle right-click on wallpaper preview."""
        if event.button == 3:  # Right mouse button
            child = self.flowbox.get_child_at_pos(event.x, event.y)
            if child:
                wallpaper_id = child.get_child().wallpaper_id
                menu = WallpaperContextMenu(self, wallpaper_id)
                menu.show_all()
                menu.popup_at_pointer(event)
                return True
        return False

    def on_destroy(self, window):
        """Clean up before exit"""
        self.log.info("Shutting down...")
        # Don't stop wallpaper on exit - let it continue running
        Gtk.main_quit()

    def on_volume_changed(self, scale: Gtk.Scale) -> None:
        """Handle volume scale changes."""
        volume = scale.get_value()
        
        # Update settings
        self.settings['volume'] = volume
        
        # Update command options based on volume
        if volume == 0:
            # Volume is zero, pass --silent option
            if self.engine.current_wallpaper:
                success, cmd = self._load_wallpaper(self.engine.current_wallpaper, mute=True)
                if success and cmd:
                    self.update_command_status(cmd)
        else:
            # Pass the volume value
            if self.engine.current_wallpaper:
                success, cmd = self._load_wallpaper(self.engine.current_wallpaper, volume=int(volume))
                if success and cmd:
                    self.update_command_status(cmd)

    def update_command_status(self, command):
        """Update status bar with last command"""
        self.statusbar.pop(self.command_context)
        self.statusbar.push(self.command_context, f"Last command: {' '.join(map(str, command))}")

    def load_settings(self):
        """Load settings from config file"""
        config_dir = os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
        config_file = os.path.join(config_dir, "settings.json")
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    saved_settings = json.load(f)
                    # Update defaults with saved settings
                    self.settings.update(saved_settings)
                    self.log.debug(f"Loaded settings: {self.settings}")
        except Exception as e:
            self.log.error(f"Failed to load settings: {e}")

    def save_settings(self):
        """Save settings to config file"""
        config_dir = os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
        config_file = os.path.join(config_dir, "settings.json")
        
        try:
            # Create config directory if it doesn't exist
            os.makedirs(config_dir, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
                self.log.debug(f"Saved settings: {self.settings}")
        except Exception as e:
            self.log.error(f"Failed to save settings: {e}")

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for navigation and control."""
        accel = Gtk.AccelGroup()
        self.add_accel_group(accel)
        
        # Left/Right arrows for navigation
        key, mod = Gtk.accelerator_parse("Left")
        accel.connect(key, mod, Gtk.AccelFlags.VISIBLE, 
                     lambda *x: self.on_prev_clicked(None))
        
        key, mod = Gtk.accelerator_parse("Right") 
        accel.connect(key, mod, Gtk.AccelFlags.VISIBLE,
                     lambda *x: self.on_next_clicked(None))
        
        # R for random
        key, mod = Gtk.accelerator_parse("r")
        accel.connect(key, mod, Gtk.AccelFlags.VISIBLE,
                     lambda *x: self.on_random_clicked(None))
        
        # S for settings
        key, mod = Gtk.accelerator_parse("s")
        accel.connect(key, mod, Gtk.AccelFlags.VISIBLE,
                     lambda *x: self.on_settings_clicked(None))

    def _validate_state(self):
        """Validate critical runtime state."""
        issues = []
        
        if not self.engine.wpe_path:
            issues.append("WPE executable not found")
        if not self.engine.display:
            issues.append("No display detected") 
        if not self.engine.wallpaper_dir:
            issues.append("Wallpaper directory not found")
        
        if issues:
            self.log.error(f"State validation failed: {', '.join(issues)}")
            return False
        return True

    def _verify_paths(self):
        """Verify all required paths exist."""
        paths = {
            'wpe': self.engine.wpe_path,
            'wallpapers': self.engine.wallpaper_dir,
            'config': os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
        }
        
        missing = []
        for name, path in paths.items():
            if not path:  # Check if path is None or empty
                missing.append(f"{name} path not configured")
                continue
            if not os.path.exists(path):
                missing.append(f"{name} path does not exist: {path}")
        
        if missing:
            self.log.error("Path verification failed:\n - " + "\n - ".join(missing))
            return False
        return True

    def _check_permissions(self):
        """Verify required file permissions."""
        try:
            # Check WPE executable
            if not os.access(self.engine.wpe_path, os.X_OK):
                self.log.error(f"WPE not executable: {self.engine.wpe_path}")
                return False
            
            # Check wallpaper dir read access  
            if not os.access(self.engine.wallpaper_dir, os.R_OK):
                self.log.error(f"Cannot read wallpaper dir: {self.engine.wallpaper_dir}")
                return False
            
            # Check config dir write access
            config_dir = os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
            if not os.access(config_dir, os.W_OK):
                self.log.error(f"Cannot write to config dir: {config_dir}")
                return False
            
            return True
        
        except Exception as e:
            self.log.error(f"Permission check failed: {e}")
            return False

class WallpaperContextMenu(Gtk.Menu):
    """Context menu for wallpaper options."""

    def __init__(self, parent: WallpaperWindow, wallpaper_id: str):
        super().__init__()
        self.parent = parent
        self.wallpaper_id = wallpaper_id

        # Add menu items
        self.add_item("Set as Wallpaper", self.on_set_as_wallpaper)
        if wallpaper_id in self.parent.directory_manager.blacklist:
            self.add_item("Remove from Blacklist", self.on_unblacklist)
        else:
            self.add_item("Add to Blacklist", self.on_blacklist)

    def add_item(self, label: str, callback: Callable) -> None:
        """Add an item to the context menu."""
        item = Gtk.MenuItem(label=label)
        item.connect("activate", callback)
        self.append(item)

    def on_set_as_wallpaper(self, widget: Gtk.MenuItem) -> None:
        """Handle setting the wallpaper."""
        success, cmd = self.parent._load_wallpaper(self.wallpaper_id)
        if success:
            self.parent.update_current_wallpaper(self.wallpaper_id)
            if cmd:
                self.parent.update_command_status(cmd)

    def on_blacklist(self, widget: Gtk.MenuItem) -> None:
        """Handle blacklisting the wallpaper."""
        self.parent.directory_manager.add_to_blacklist(self.wallpaper_id)
        self.parent.load_wallpapers()  # Reload to remove blacklisted wallpaper

    def on_unblacklist(self, widget: Gtk.MenuItem) -> None:
        """Handle removing the wallpaper from blacklist."""
        self.parent.directory_manager.remove_from_blacklist(self.wallpaper_id)
        self.parent.load_wallpapers()  # Reload to show unblacklisted wallpaper

class SettingsDialog(Gtk.Dialog):
    """Settings dialog for configuring application settings."""

    def __init__(self, parent: WallpaperWindow, settings: dict) -> None:
        """Initialize settings dialog.

        Args:
            parent: Parent window
            settings: Current application settings
        """
        super().__init__(title="Settings", parent=parent, flags=0)
        self.parent = parent
        self.set_default_size(700, 500)

        # Create notebook for tabbed interface
        self.notebook = Gtk.Notebook()
        self.get_content_area().pack_start(self.notebook, True, True, 0)

        # Add tabs
        self._create_general_tab()
        self._create_directories_tab()
        self._create_performance_tab()
        self._create_audio_tab()

        # Add buttons
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )

        self.connect("response", self.on_response)
        self.show_all()

    def _create_general_tab(self) -> None:
        """Create general settings tab."""
        grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        
        # WPE Path selection
        path_label = Gtk.Label(label="WPE Path:", halign=Gtk.Align.END)
        self.wpe_path_entry = Gtk.Entry()
        self.wpe_path_entry.set_text(self.parent.engine.wpe_path or "")
        browse_button = Gtk.Button(label="Browse")
        browse_button.connect("clicked", self.on_browse_wpe_clicked)
        
        grid.attach(path_label, 0, 0, 1, 1)
        grid.attach(self.wpe_path_entry, 1, 0, 1, 1)
        grid.attach(browse_button, 2, 0, 1, 1)

        # Add to notebook
        label = Gtk.Label(label="General")
        self.notebook.append_page(grid, label)

    def _create_directories_tab(self) -> None:
        """Create directories management tab."""
        grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        
        # Directory list with statistics
        self.directory_store = Gtk.ListStore(bool, str, int, int, int, str)  # enabled, path, total, blacklisted, active, last scan
        self.directory_view = Gtk.TreeView(model=self.directory_store)
        
        # Add columns
        columns = [
            ("Enabled", 0, True),  # Toggle column
            ("Directory", 1, True),  # Text column, expandable
            ("Total", 2, False),
            ("Blacklisted", 3, False),
            ("Active", 4, False),
            ("Last Scan", 5, False)
        ]
        
        for title, col_id, expand in columns:
            if col_id == 0:  # Enabled column
                renderer = Gtk.CellRendererToggle()
                renderer.connect("toggled", self.on_directory_toggled)
                column = Gtk.TreeViewColumn(title, renderer, active=0)
            else:
                renderer = Gtk.CellRendererText()
                column = Gtk.TreeViewColumn(title, renderer, text=col_id)
                column.set_expand(expand)
            
            self.directory_view.append_column(column)
        
        # Scrolled window for directory list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        scrolled.add(self.directory_view)
        
        grid.attach(scrolled, 0, 0, 3, 1)
        
        # Directory management buttons
        button_box = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.START)
        button_box.set_spacing(6)
        
        add_button = Gtk.Button(label="Add Directory")
        add_button.connect("clicked", self.on_add_directory_clicked)
        remove_button = Gtk.Button(label="Remove Directory")
        remove_button.connect("clicked", self.on_remove_directory_clicked)
        scan_button = Gtk.Button(label="Scan All")
        scan_button.connect("clicked", self.on_scan_all_clicked)
        
        button_box.add(add_button)
        button_box.add(remove_button)
        button_box.add(scan_button)
        
        grid.attach(button_box, 0, 1, 3, 1)
        
        # Add to notebook
        label = Gtk.Label(label="Directories")
        self.notebook.append_page(grid, label)
        
        # Populate directory list
        self._populate_directory_list()

    def _create_performance_tab(self) -> None:
        """Create performance settings tab."""
        grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        
        # FPS settings
        fps_label = Gtk.Label(label="Default FPS:", halign=Gtk.Align.END)
        self.fps_spin = Gtk.SpinButton.new_with_range(1, 240, 1)
        self.fps_spin.set_value(self.parent.settings.get('fps', 60))
        
        grid.attach(fps_label, 0, 0, 1, 1)
        grid.attach(self.fps_spin, 1, 0, 1, 1)
        
        # Process priority
        priority_label = Gtk.Label(label="Process Priority:", halign=Gtk.Align.END)
        self.priority_combo = Gtk.ComboBoxText()
        for priority in ["Low", "Normal", "High"]:
            self.priority_combo.append_text(priority)
        self.priority_combo.set_active(1)  # Default to Normal
        
        grid.attach(priority_label, 0, 1, 1, 1)
        grid.attach(self.priority_combo, 1, 1, 1, 1)
        
        # Add to notebook
        label = Gtk.Label(label="Performance")
        self.notebook.append_page(grid, label)

    def _create_audio_tab(self) -> None:
        """Create audio settings tab."""
        grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        
        # Volume settings
        volume_label = Gtk.Label(label="Default Volume:", halign=Gtk.Align.END)
        self.volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.volume_scale.set_value(self.parent.settings.get('volume', 100))
        
        grid.attach(volume_label, 0, 0, 1, 1)
        grid.attach(self.volume_scale, 1, 0, 2, 1)
        
        # Audio processing switches
        switches = [
            ("Keep Playing When Other Apps Play Sound", "no_automute"),
            ("Disable Audio Effects", "no_audio_processing")
        ]
        
        for i, (label, setting) in enumerate(switches, start=1):
            switch_label = Gtk.Label(label=label + ":", halign=Gtk.Align.END)
            switch = Gtk.Switch()
            switch.set_active(self.parent.settings.get(setting, False))
            setattr(self, f"{setting}_switch", switch)
            
            grid.attach(switch_label, 0, i, 1, 1)
            grid.attach(switch, 1, i, 1, 1)
        
        # Add to notebook
        label = Gtk.Label(label="Audio")
        self.notebook.append_page(grid, label)

    def _populate_directory_list(self) -> None:
        """Populate the directory list with current directories and their stats."""
        self.directory_store.clear()
        for path, info in self.parent.directory_manager.directories.items():
            stats = self.parent.directory_manager.get_directory_stats(path)
            self.directory_store.append([
                info['enabled'],
                path,
                stats['total_count'],
                stats['blacklisted_count'],
                stats['active_count'],
                stats['last_scan'].split('T')[0] if stats.get('last_scan') else 'Never'
            ])

    def on_directory_toggled(self, cell: Gtk.CellRendererToggle, path: str) -> None:
        """Handle toggling of directory enabled state."""
        iter = self.directory_store.get_iter(path)
        enabled = not self.directory_store[iter][0]
        directory_path = self.directory_store[iter][1]
        
        self.directory_store[iter][0] = enabled
        self.parent.directory_manager.toggle_directory(directory_path, enabled)

    def on_browse_wpe_clicked(self, button: Gtk.Button) -> None:
        """Handle browsing for WPE executable."""
        dialog = Gtk.FileChooserDialog(
            title="Select WPE Executable",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.wpe_path_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def on_add_directory_clicked(self, button: Gtk.Button) -> None:
        """Handle adding a new directory."""
        dialog = Gtk.FileChooserDialog(
            title="Select Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            path = dialog.get_filename()
            self.parent.directory_manager.add_scan_path(path)
            self._populate_directory_list()
        dialog.destroy()

    def on_remove_directory_clicked(self, button: Gtk.Button) -> None:
        """Handle removing a directory."""
        selection = self.directory_view.get_selection()
        model, iter = selection.get_selected()
        if iter:
            path = model[iter][1]
            confirm = Gtk.MessageDialog(
                transient_for=self,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Remove directory {path}?"
            )
            response = confirm.run()
            confirm.destroy()
            
            if response == Gtk.ResponseType.YES:
                self.parent.directory_manager.remove_scan_path(path)
                self._populate_directory_list()

    def on_scan_all_clicked(self, button: Gtk.Button) -> None:
        """Handle scanning all directories."""
        self.parent.directory_manager.rescan_all()
        self._populate_directory_list()

    def on_response(self, dialog: Gtk.Dialog, response: int) -> None:
        """Handle dialog response."""
        if response == Gtk.ResponseType.OK:
            # Update settings
            self.parent.settings.update({
                'fps': self.fps_spin.get_value_as_int(),
                'volume': int(self.volume_scale.get_value()),
                'no_automute': self.no_automute_switch.get_active(),
                'no_audio_processing': self.no_audio_processing_switch.get_active(),
                'process_priority': self.priority_combo.get_active_text()
            })
            
            # Update WPE path if changed
            new_wpe_path = self.wpe_path_entry.get_text()
            if new_wpe_path != self.parent.engine.wpe_path:
                self.parent.engine.wpe_path = new_wpe_path
                
            # Save settings
            self.parent.save_settings()

class WallpaperDirectoryManager:
    """Manages wallpaper directories for the application.
    
    This class handles multiple wallpaper directories, including scanning,
    enabling/disabling, and tracking statistics for each directory.
    """

    def __init__(self):
        self.directories = {}  # Dictionary to hold directory paths and their states
        self.blacklist = set()  # Set of blacklisted wallpaper IDs
        self.load_config()

    def add_scan_path(self, path: str) -> None:
        """Add a directory path to be scanned for wallpapers.
        
        Args:
            path: The directory path to add and scan
        """
        if path not in self.directories:
            self.directories[path] = {
                'enabled': True,
                'total_count': 0,
                'blacklisted_count': 0,
                'last_scan': None,
                'wallpapers': set()
            }
            self._scan_directory(path)
            self.save_config()

    def remove_scan_path(self, path: str) -> None:
        """Remove a directory path from scanning.
        
        Args:
            path: The directory path to remove
        """
        if path in self.directories:
            del self.directories[path]
            self.save_config()

    def toggle_directory(self, path: str, enabled: bool) -> None:
        """Toggle a directory's enabled state.
        
        Args:
            path: The directory path to toggle
            enabled: The new enabled state
        """
        if path in self.directories:
            self.directories[path]['enabled'] = enabled
            self.save_config()

    def get_enabled_directories(self) -> list[str]:
        """Return a list of enabled directory paths.
        
        Returns:
            List of enabled directory paths
        """
        return [path for path, info in self.directories.items() if info['enabled']]

    def get_directory_stats(self, path: str) -> dict:
        """Get statistics for a directory.
        
        Args:
            path: The directory path to get stats for
            
        Returns:
            Dictionary containing directory statistics
        """
        if path in self.directories:
            return {
                'total_count': self.directories[path]['total_count'],
                'blacklisted_count': self.directories[path]['blacklisted_count'],
                'active_count': self.directories[path]['total_count'] - self.directories[path]['blacklisted_count'],
                'last_scan': self.directories[path]['last_scan']
            }
        return {}

    def _scan_directory(self, path: str) -> None:
        """Scan the specified directory for wallpapers and update statistics.
        
        Args:
            path: The directory path to scan
        """
        if not os.path.exists(path):
            return

        wallpapers = set()
        blacklisted = 0
        
        # Walk through directory looking for preview files which indicate wallpapers
        for root, _, files in os.walk(path):
            for file in files:
                if file.startswith('preview') and any(file.endswith(ext) for ext in ['.gif', '.png', '.jpg', '.jpeg', '.webp']):
                    wallpaper_id = os.path.basename(os.path.dirname(os.path.join(root, file)))
                    wallpapers.add(wallpaper_id)
                    if wallpaper_id in self.blacklist:
                        blacklisted += 1

        self.directories[path].update({
            'total_count': len(wallpapers),
            'blacklisted_count': blacklisted,
            'last_scan': datetime.now().isoformat(),
            'wallpapers': wallpapers
        })

    def add_to_blacklist(self, wallpaper_id: str) -> None:
        """Add a wallpaper to the blacklist.
        
        Args:
            wallpaper_id: The wallpaper ID to blacklist
        """
        self.blacklist.add(wallpaper_id)
        # Update counts in directories
        for dir_info in self.directories.values():
            if wallpaper_id in dir_info['wallpapers']:
                dir_info['blacklisted_count'] += 1
        self.save_config()

    def remove_from_blacklist(self, wallpaper_id: str) -> None:
        """Remove a wallpaper from the blacklist.
        
        Args:
            wallpaper_id: The wallpaper ID to unblacklist
        """
        if wallpaper_id in self.blacklist:
            self.blacklist.remove(wallpaper_id)
            # Update counts in directories
            for dir_info in self.directories.values():
                if wallpaper_id in dir_info['wallpapers']:
                    dir_info['blacklisted_count'] -= 1
            self.save_config()

    def load_config(self) -> None:
        """Load directory configuration from file."""
        config_dir = os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
        config_file = os.path.join(config_dir, "directories.json")
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.directories = data.get('directories', {})
                    self.blacklist = set(data.get('blacklist', []))
        except Exception as e:
            logging.error(f"Failed to load directory config: {e}")

    def save_config(self) -> None:
        """Save directory configuration to file."""
        config_dir = os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
        config_file = os.path.join(config_dir, "directories.json")
        
        try:
            os.makedirs(config_dir, exist_ok=True)
            with open(config_file, 'w') as f:
                # Convert sets to lists for JSON serialization
                directories = {
                    path: {
                        **info,
                        'wallpapers': list(info['wallpapers'])
                    }
                    for path, info in self.directories.items()
                }
                json.dump({
                    'directories': directories,
                    'blacklist': list(self.blacklist)
                }, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save directory config: {e}")

    def rescan_all(self) -> None:
        """Rescan all directories to update wallpaper counts."""
        for path in list(self.directories.keys()):
            self._scan_directory(path)
        self.save_config()

    def get_all_wallpapers(self) -> set[str]:
        """Get all wallpapers from enabled directories.
        
        Returns:
            Set of wallpaper IDs from enabled directories
        """
        wallpapers = set()
        for path, info in self.directories.items():
            if info['enabled']:
                wallpapers.update(info['wallpapers'])
        return wallpapers - self.blacklist

class BlacklistDialog(Gtk.Dialog):
    """Dialog for managing blacklisted wallpapers."""

    def __init__(self, parent: WallpaperWindow):
        super().__init__(title="Manage Blacklist", parent=parent, flags=0)
        self.parent = parent
        self.set_default_size(400, 300)

        # Create a grid for all settings
        self.settings_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        self.get_content_area().add(self.settings_grid)

        # Initialize settings
        self.current_settings = getattr(parent, 'settings', self.default_settings())
        self._create_blacklist_settings()  # Ensure this method exists

        # Add buttons
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
                         Gtk.STOCK_SAVE, Gtk.ResponseType.OK)

        self.connect("response", self.on_response)
        self.show_all()

    def _create_blacklist_settings(self) -> None:
        """Create settings for managing the blacklist."""
        # Implement the logic for managing the blacklist here
        pass  # Placeholder for actual implementation

    def on_response(self, dialog: Gtk.Dialog, response: int) -> None:
        """Handle dialog response."""
        if response == Gtk.ResponseType.OK:
            # Logic to save blacklist changes
            pass  # Placeholder for actual implementation

        # Close the dialog
        self.destroy()

def main():
    # Setup logging with more verbose output
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('wallpaper-engine.log')
        ]
    )
    
    logging.info("Starting Linux Wallpaper Engine GTK...")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Linux Wallpaper Engine GTK')
    parser.add_argument('--fps', type=int, default=60)
    parser.add_argument('--volume', type=int, default=100)
    parser.add_argument('--mute', action='store_true')
    parser.add_argument('--disable-mouse', action='store_true')
    parser.add_argument('--no-automute', action='store_true')
    parser.add_argument('--no-audio-processing', action='store_true')
    parser.add_argument('--no-fullscreen-pause', action='store_true')
    parser.add_argument('--scaling', choices=['default', 'stretch', 'fit', 'fill'], default='default')
    parser.add_argument('--clamping', choices=['clamp', 'border', 'repeat'], default='clamp')
    args = parser.parse_args()
    
    # Check for config directory and welcome flag
    config_dir = os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
    welcome_flag = os.path.join(config_dir, ".welcomed")
    wpe_path = None
    
    if not os.path.exists(welcome_flag):
        dialog = WelcomeDialog()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            wpe_path = dialog.path_entry.get_text()
            if wpe_path:
                os.makedirs(config_dir, exist_ok=True)
                with open(welcome_flag, 'w') as f:
                    f.write(wpe_path)
        else:
            dialog.destroy()
            sys.exit(0)
        
        dialog.destroy()
    else:
        try:
            with open(welcome_flag, 'r') as f:
                wpe_path = f.read().strip()
        except Exception as e:
            logging.error(f"Failed to read WPE path: {e}")
    
    try:
        win = WallpaperWindow(wpe_path=wpe_path, initial_settings={
            'fps': args.fps,
            'volume': args.volume,
            'mouse_enabled': args.disable_mouse,
            'auto_rotation': False,
            'rotation_interval': 15,
            'no_automute': args.no_automute,
            'no_audio_processing': args.no_audio_processing,
            'no_fullscreen_pause': args.no_fullscreen_pause,
            'scaling': args.scaling,
            'clamping': args.clamping
        })
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        
        logging.info("Entering GTK main loop")
        Gtk.main()
        
    except RuntimeError as e:
        logging.error(f"Failed to start application: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

def run_integrated_tests() -> None:
    """Integrated test suite for linux-wallpaperengine-gtk."""
    import pytest
    from typing import Generator
    from pathlib import Path
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture

    class TestSettingsDialog:
        """Test suite for settings dialog functionality."""
        
        @pytest.fixture
        def mock_window(self, tmp_path: Path) -> Generator[WallpaperWindow, None, None]:
            """Create test window instance."""
            win = WallpaperWindow()
            yield win
            win.destroy()

        @pytest.fixture
        def dialog(self, mock_window: WallpaperWindow) -> Generator[SettingsDialog, None, None]:
            """Create test settings dialog instance."""
            dialog = SettingsDialog(mock_window, mock_window.settings)
            yield dialog
            dialog.destroy()

        def test_directory_management(self, dialog: SettingsDialog, tmp_path: Path) -> None:
            """Test directory management functionality."""
            # Add test directory
            test_dir = tmp_path / "test_wallpapers"
            test_dir.mkdir()
            
            # Add directory through UI
            dialog.parent.directory_manager.add_scan_path(str(test_dir))
            dialog._populate_directory_list()
            
            # Verify directory is listed
            found = False
            for row in dialog.directory_store:
                if row[1] == str(test_dir):
                    found = True
                    assert row[0]  # Enabled by default
                    break
            assert found

        def test_settings_persistence(self, dialog: SettingsDialog) -> None:
            """Test settings persistence."""
            # Change some settings
            dialog.fps_spin.set_value(30)
            dialog.volume_scale.set_value(50)
            dialog.no_automute_switch.set_active(True)
            
            # Simulate OK response
            dialog.on_response(dialog, Gtk.ResponseType.OK)
            
            # Verify settings were updated
            assert dialog.parent.settings['fps'] == 30
            assert dialog.parent.settings['volume'] == 50
            assert dialog.parent.settings['no_automute']

        def test_directory_toggle(self, dialog: SettingsDialog, tmp_path: Path) -> None:
            """Test directory enable/disable functionality."""
            # Add test directory
            test_dir = tmp_path / "test_wallpapers"
            test_dir.mkdir()
            dialog.parent.directory_manager.add_scan_path(str(test_dir))
            dialog._populate_directory_list()
            
            # Find and toggle the directory
            for row in dialog.directory_store:
                if row[1] == str(test_dir):
                    # Simulate toggle
                    dialog.on_directory_toggled(None, row.path)
                    assert not row[0]  # Should be disabled
                    assert not dialog.parent.directory_manager.directories[str(test_dir)]['enabled']
                    break

if __name__ == "__main__":
    main()
else:
    run_integrated_tests()
