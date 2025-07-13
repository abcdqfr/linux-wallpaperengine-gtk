#!/usr/bin/env python3
"""
Linux Wallpaper Engine GTK Frontend
A standalone GTK interface for linux-wallpaperengine
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk
import os, json, subprocess, threading, logging, time
from pathlib import Path
import random
import argparse

class WallpaperEngine:
    """Core wallpaper engine functionality"""
    
    def __init__(self):
        self.log = logging.getLogger('WallpaperEngine')
        
        # Check for Wayland compatibility
        if self._is_wayland():
            self.log.error("WAYLAND DETECTED - Linux Wallpaper Engine is NOT compatible with Wayland!")
            self.log.error("Please switch to X11 session or the wallpapers will not work properly.")
        
        self.display = self._detect_display()
        self.wpe_path = self._find_wpe_path()
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
            "./linux-wallpaperengine",
            # System paths
            "/usr/local/bin/linux-wallpaperengine",
            "/usr/bin/linux-wallpaperengine",
            "/opt/linux-wallpaperengine/linux-wallpaperengine"
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
            
            # Check if custom arguments contain single-process mode
            using_single_process = (options.get('enable_custom_args') and 
                                  options.get('custom_args') and 
                                  '--single-process' in options.get('custom_args', ''))
            
            self.log.debug(f"Single-process detection: enable_custom_args={options.get('enable_custom_args')}, custom_args='{options.get('custom_args')}', using_single_process={using_single_process}")
            
            # Add common options (skip problematic ones if using single-process mode)
            if not using_single_process:
                # Full argument set for normal mode
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
            else:
                # Limited argument set for single-process mode (exclude scaling/clamping)
                self.log.info("Single-process mode detected - excluding problematic scaling/clamping arguments")
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
                # Skip scaling and clamping - they break argument parsing in single-process mode
            
            # Add custom arguments if enabled
            if options.get('enable_custom_args') and options.get('custom_args'):
                custom_args = options['custom_args'].strip()
                if custom_args:
                    # Split custom arguments properly (handle quoted strings)
                    import shlex
                    try:
                        custom_args_list = shlex.split(custom_args)
                        cmd.extend(custom_args_list)
                        self.log.info(f"Added custom arguments: {custom_args_list}")
                    except ValueError as e:
                        self.log.error(f"Invalid custom arguments syntax: {e}")
            
            # Add display and wallpaper ID
            cmd.extend(['--screen-root', self.display, wallpaper_id])
            
            self.log.info(f"Running command: {' '.join(map(str, cmd))}")
            
            # Setup environment variables
            env = os.environ.copy()
            
            # Add LD_PRELOAD if enabled
            if options.get('enable_ld_preload'):
                libcef_path = os.path.join(wpe_dir, 'libcef.so')
                if os.path.exists(libcef_path):
                    env['LD_PRELOAD'] = libcef_path
                    self.log.info(f"Added LD_PRELOAD: {libcef_path}")
                else:
                    self.log.warning(f"libcef.so not found at {libcef_path}, skipping LD_PRELOAD")
            
            # Create new process with stable configuration
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
                cwd=wpe_dir,
                env=env
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

    def _is_wayland(self):
        """Check if running under Wayland"""
        return os.environ.get('WAYLAND_DISPLAY') is not None or \
               os.environ.get('XDG_SESSION_TYPE') == 'wayland'

class WallpaperWindow(Gtk.Window):
    def __init__(self, initial_settings=None):
        super().__init__(title="Linux Wallpaper Engine")
        self.set_default_size(800, 600)
        
        # Initialize engine
        self.engine = WallpaperEngine()
        
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
            'clamping': 'clamp',
            'enable_custom_args': False,
            'custom_args': '',
            'enable_ld_preload': False
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
        
        # Check if setup is needed
        GLib.idle_add(self.check_initial_setup)

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
        
        # Mute toggle with icon
        self.mute_button = Gtk.ToggleButton()
        self.volume_icon = Gtk.Image.new_from_icon_name("audio-volume-high-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.mute_button.add(self.volume_icon)
        self.mute_button.set_tooltip_text("Toggle Mute")
        self.mute_button.connect("toggled", self.on_mute_toggled)
        vol_box.pack_start(self.mute_button, False, False, 0)
        
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
        scale.set_size_request(100, -1)  # Set width, keep default height
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.set_digits(0)  # Show as integer percentage
        scale.connect("value-changed", self.on_preview_scale_changed)
        scale_box.pack_start(scale, True, True, 0)
        
        scale_item.add(scale_box)
        toolbar.insert(scale_item, -1)
        
        # Control buttons
        buttons = [
            ("media-skip-backward-symbolic", "Previous", self.on_prev_clicked),
            ("media-skip-forward-symbolic", "Next", self.on_next_clicked),
            ("media-playlist-shuffle-symbolic", "Random", self.on_random_clicked),
            ("view-refresh-symbolic", "Refresh Wallpapers", self.on_refresh_clicked),
            ("applications-system-symbolic", "Setup Paths", self.on_setup_clicked),
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

    def load_wallpapers(self):
        """Load and display wallpaper previews"""
        def load_preview(wallpaper_id):
            wallpaper_path = os.path.join(self.engine.wallpaper_dir, wallpaper_id)
            
            # Skip if directory doesn't exist
            if not os.path.exists(wallpaper_path):
                return
            
            preview_path = None
            
            # Look for preview image
            for ext in ['.gif', '.png', '.jpg', '.webp', '.jpeg']:
                path = os.path.join(wallpaper_path, f'preview{ext}')
                if os.path.exists(path):
                    preview_path = path
                    break
            
            # If no preview.* file found, look for any image file as fallback
            if not preview_path:
                for filename in os.listdir(wallpaper_path):
                    if filename.lower().endswith(('.gif', '.png', '.jpg', '.jpeg', '.webp')):
                        preview_path = os.path.join(wallpaper_path, filename)
                        break
            
            # Skip if no image found at all
            if not preview_path:
                return
                
            # Load actual image preview
            def add_preview():
                try:
                    box = Gtk.Box()
                    box.set_margin_start(2)
                    box.set_margin_end(2)
                    box.set_margin_top(2)
                    box.set_margin_bottom(2)
                    
                    # Handle GIF animations
                    if preview_path.lower().endswith('.gif'):
                        try:
                            animation = GdkPixbuf.PixbufAnimation.new_from_file(preview_path)
                            if animation.is_static_image():
                                pixbuf = animation.get_static_image().scale_simple(
                                    self.preview_width, self.preview_height, GdkPixbuf.InterpType.BILINEAR)
                                image = Gtk.Image.new_from_pixbuf(pixbuf)
                            else:
                                # Animated GIF
                                iter = animation.get_iter(None)
                                first_frame = iter.get_pixbuf()
                                scale_x = self.preview_width / first_frame.get_width()
                                scale_y = self.preview_height / first_frame.get_height()
                                scale = min(scale_x, scale_y)
                                
                                frames = []
                                iter = animation.get_iter(None)
                                while True:
                                    pixbuf = iter.get_pixbuf()
                                    new_width = int(pixbuf.get_width() * scale)
                                    new_height = int(pixbuf.get_height() * scale)
                                    scaled_frame = pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)
                                    frames.append(scaled_frame)
                                    if not iter.advance():
                                        break
                                
                                image = Gtk.Image()
                                current_frame = 0
                                
                                def update_frame():
                                    nonlocal current_frame
                                    if len(frames) > 0:
                                        image.set_from_pixbuf(frames[current_frame])
                                        current_frame = (current_frame + 1) % len(frames)
                                    return True
                                
                                GLib.timeout_add(50, update_frame)
                        except Exception:
                            # Fallback to static image
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                                preview_path, self.preview_width, self.preview_height, True)
                            image = Gtk.Image.new_from_pixbuf(pixbuf)
                    else:
                        # Static images
                        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                            preview_path, self.preview_width, self.preview_height, True)
                        image = Gtk.Image.new_from_pixbuf(pixbuf)
                    
                    box.add(image)
                    box.wallpaper_id = wallpaper_id
                    self.flowbox.add(box)
                    box.show_all()
                    
                    if wallpaper_id == self.engine.current_wallpaper:
                        self.highlight_current_wallpaper(box)
                        
                except Exception as e:
                    self.log.error(f"Failed to load preview {preview_path}: {e}")
            
            GLib.idle_add(add_preview)

        # Clear existing previews
        self.flowbox.foreach(lambda w: w.destroy())
        
        # Load new previews 
        wallpapers = self.engine.get_wallpaper_list()
        self.status_label.set_text(f"Loading {len(wallpapers)} wallpapers...")
        
        for i, wallpaper_id in enumerate(wallpapers):
            def load_with_delay(wid):
                thread = threading.Thread(target=load_preview, args=(wid,))
                thread.daemon = True
                thread.start()
            
            GLib.timeout_add(i * 5, lambda wid=wallpaper_id: load_with_delay(wid) or False)

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
        """Handle wallpaper selection"""
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
            clamping=self.settings['clamping'],
            enable_custom_args=self.settings['enable_custom_args'],
            custom_args=self.settings['custom_args'],
            enable_ld_preload=self.settings['enable_ld_preload']
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

    def on_refresh_clicked(self, button):
        """Refresh wallpaper list"""
        self.status_label.set_text("Refreshing wallpaper list...")
        self.load_wallpapers()
        self.status_label.set_text("Wallpaper list refreshed")

    def on_setup_clicked(self, button):
        """Open setup dialog for path configuration"""
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
        """Open settings dialog"""
        dialog = SettingsDialog(self)
        response = dialog.run()
        
        if response != Gtk.ResponseType.OK:
            dialog.destroy()  # Destroy dialog first to prevent GTK warnings
            return  # Don't apply settings if cancelled
            
        try:
            # Save settings including paths
            settings = {
                'fps': dialog.fps_spin.get_value_as_int(),
                'volume': self.settings['volume'],  # Keep current volume
                'mute': self.settings['mute'],      # Keep current mute state
                'mouse_enabled': dialog.mouse_switch.get_active(),
                'auto_rotation': dialog.rotation_switch.get_active(),
                'rotation_interval': dialog.interval_spin.get_value_as_int(),
                'no_automute': dialog.no_automute_switch.get_active(),
                'no_audio_processing': dialog.no_audio_processing_switch.get_active(),
                'no_fullscreen_pause': dialog.no_fullscreen_pause_switch.get_active(),
                'scaling': dialog.scaling_combo.get_active_text(),
                'clamping': dialog.clamping_combo.get_active_text(),
                'enable_custom_args': dialog.custom_args_switch.get_active(),
                'custom_args': dialog.custom_args_entry.get_text().strip(),
                'enable_ld_preload': dialog.ld_preload_switch.get_active()
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
        """Apply settings to current and future wallpapers"""
        # Store settings
        self.settings = settings
        self.save_settings()  # Save settings to file
        
        # Update current wallpaper if running
        if self.engine.current_wallpaper:
            success, cmd = self.engine.run_wallpaper(
                self.engine.current_wallpaper,
                fps=settings['fps'],
                volume=settings['volume'],
                mute=settings['mute'],
                no_automute=settings['no_automute'],
                no_audio_processing=settings['no_audio_processing'],
                disable_mouse=settings['mouse_enabled'],
                no_fullscreen_pause=settings['no_fullscreen_pause'],
                scaling=settings['scaling'],
                clamping=settings['clamping'],
                enable_custom_args=settings['enable_custom_args'],
                custom_args=settings['custom_args'],
                enable_ld_preload=settings['enable_ld_preload']
            )
            if success and cmd:
                self.update_command_status(cmd)
        
        # Handle auto-rotation
        if settings['auto_rotation']:
            self.start_playlist_rotation(settings['rotation_interval'])
        else:
            self.stop_playlist_rotation()
    
    def start_playlist_rotation(self, interval):
        """Start automatic wallpaper rotation"""
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
        """Stop automatic wallpaper rotation"""
        if self.playlist_timeout:
            GLib.source_remove(self.playlist_timeout)
            self.playlist_timeout = None
        self.playlist_active = False
    
    def on_right_click(self, widget, event):
        """Handle right-click on wallpapers"""
        if event.button == 3:  # Right click
            child = widget.get_child_at_pos(event.x, event.y)
            if child:
                wallpaper_id = child.get_child().wallpaper_id
                menu = WallpaperContextMenu(self, wallpaper_id)
                menu.popup_at_pointer(event)
                return True
        return False
    
    def on_destroy(self, window):
        """Clean up before exit"""
        self.log.info("Shutting down...")
        # Don't stop wallpaper on exit - let it continue running
        Gtk.main_quit()

    def on_mute_toggled(self, button):
        """Handle mute button toggle"""
        is_muted = button.get_active()
        
        # Update settings
        self.settings['mute'] = is_muted
        
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
        """Handle volume scale changes"""
        volume = scale.get_value()
        
        # Update settings
        self.settings['volume'] = volume
        self.settings['mute'] = volume == 0
        
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
                    
                    # Load engine paths if saved
                    if 'wpe_path' in saved_settings and saved_settings['wpe_path']:
                        self.engine.wpe_path = saved_settings['wpe_path']
                        self.log.info(f"Loaded saved wallpaper engine path: {saved_settings['wpe_path']}")
                    
                    if 'wallpaper_dir' in saved_settings and saved_settings['wallpaper_dir']:
                        self.engine.wallpaper_dir = saved_settings['wallpaper_dir']
                        self.log.info(f"Loaded saved wallpaper directory: {saved_settings['wallpaper_dir']}")
                    
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
            
            # Include engine paths in settings
            settings_to_save = self.settings.copy()
            settings_to_save['wpe_path'] = self.engine.wpe_path
            settings_to_save['wallpaper_dir'] = self.engine.wallpaper_dir
            
            with open(config_file, 'w') as f:
                json.dump(settings_to_save, f, indent=4)
                self.log.debug(f"Saved settings with paths: {settings_to_save}")
        except Exception as e:
            self.log.error(f"Failed to save settings: {e}")

    def check_initial_setup(self):
        """Check if initial setup is needed"""
        # Check for Wayland first
        if self.engine._is_wayland():
            dialog = Gtk.MessageDialog(
                parent=self,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Wayland Session Detected!"
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
                text="Setup Required"
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

class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(
            title="Settings",
            parent=parent,
            flags=0
        )
        self.add_buttons(
            "Cancel", Gtk.ResponseType.CANCEL,
            "Save", Gtk.ResponseType.OK
        )
        
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
        help_label.set_markup("<i>If paths are not detected automatically, use the Browse buttons to locate:\n• linux-wallpaperengine executable\n• Steam Workshop content directory (usually ~/.steam/steam/steamapps/workshop/content/431960)</i>")
        help_label.set_line_wrap(True)
        help_label.set_max_width_chars(50)
        paths_grid.attach(help_label, 0, 2, 2, 1)
        
        # Add Advanced CEF Arguments tab (after paths configuration)
        advanced_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(advanced_grid, Gtk.Label(label="Advanced"))
        
        # Enable custom arguments
        self.custom_args_switch = Gtk.Switch()
        self.custom_args_switch.set_active(self.current_settings.get('enable_custom_args', False))
        custom_args_label = Gtk.Label(label="Enable Custom CEF Arguments:", halign=Gtk.Align.END)
        custom_args_label.set_tooltip_text("Enable custom CEF arguments for compatibility fixes and advanced options")
        advanced_grid.attach(custom_args_label, 0, 0, 1, 1)
        advanced_grid.attach(self.custom_args_switch, 1, 0, 1, 1)
        
        # Custom arguments entry
        args_label = Gtk.Label(label="Custom Arguments:", halign=Gtk.Align.END)
        self.custom_args_entry = Gtk.Entry()
        self.custom_args_entry.set_text(self.current_settings.get('custom_args', ''))
        self.custom_args_entry.set_placeholder_text("e.g., --no-sandbox --single-process")
        self.custom_args_entry.set_tooltip_text("Additional command-line arguments for linux-wallpaperengine")
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
        self.ld_preload_switch.set_active(self.current_settings.get('enable_ld_preload', False))
        ld_preload_label = Gtk.Label(label="Enable LD_PRELOAD Fix:", halign=Gtk.Align.END)
        ld_preload_label.set_tooltip_text("Preload libcef.so to fix CEF v119+ static TLS allocation issues")
        advanced_grid.attach(ld_preload_label, 0, 3, 1, 1)
        advanced_grid.attach(self.ld_preload_switch, 1, 3, 1, 1)
        
        # Help text for advanced options
        advanced_help = Gtk.Label()
        advanced_help.set_markup("<b>Advanced CEF Options Help:</b>\n\n" +
                                "<b>Intel Graphics Fix:</b> Solves CEF v119+ crashes with --no-sandbox --single-process\n" +
                                "<b>LD_PRELOAD Fix:</b> Fixes static TLS allocation issues on modern CEF versions\n" +
                                "<b>Debug Mode:</b> Enables CEF debugging and verbose logging\n" +
                                "<b>Performance Mode:</b> Optimizes for better performance on low-end systems\n\n" +
                                "<i>⚠️ These options fix known compatibility issues but may affect stability</i>")
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
        """Browse for wallpaper engine executable"""
        dialog = Gtk.FileChooserDialog(
            title="Select linux-wallpaperengine executable",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
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
        """Browse for wallpaper directory"""
        dialog = Gtk.FileChooserDialog(
            title="Select wallpaper directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Set initial directory
        if self.wallpaper_entry.get_text():
            dialog.set_current_folder(self.wallpaper_entry.get_text())
        else:
            # Try to find Steam directory
            for steam_path in ["~/.steam/steam/steamapps/workshop/content/431960",
                              "~/.local/share/Steam/steamapps/workshop/content/431960"]:
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
        """Handle selection of a preset from the advanced options combo box"""
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
        """Handle the custom arguments switch toggle"""
        is_active = switch.get_active()
        if is_active:
            self.custom_args_entry.set_sensitive(True)
            self.presets_combo.set_sensitive(True)
            self.ld_preload_switch.set_sensitive(True)
        else:
            self.custom_args_entry.set_sensitive(False)
            self.presets_combo.set_sensitive(False)
            self.ld_preload_switch.set_sensitive(False)

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

def main():
    # Setup logging with more verbose output
    logging.basicConfig(
        level=logging.DEBUG,  # Changed from INFO to DEBUG
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler('wallpaper-engine.log')  # File output
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
    
    # Create and show window
    win = WallpaperWindow(initial_settings={
        'fps': args.fps,
        'volume': args.volume,
        'mute': args.mute,
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
    
    # Start GTK main loop
    logging.info("Entering GTK main loop")
    Gtk.main()

if __name__ == "__main__":
    main()