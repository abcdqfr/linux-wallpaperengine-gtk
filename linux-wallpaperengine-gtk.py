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
            "~/linux-wallpaperengine/build/linux-wallpaperengine",
            "~/src/linux-wallpaperengine/build/linux-wallpaperengine",
            "/usr/local/bin/linux-wallpaperengine"
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
            preview_path = None
            wallpaper_path = os.path.join(self.engine.wallpaper_dir, wallpaper_id)
            
            # Look for preview image
            for ext in ['.gif', '.png', '.jpg', '.webp', '.jpeg']:  # Prioritize GIFs
                path = os.path.join(wallpaper_path, f'preview{ext}')
                if os.path.exists(path):
                    preview_path = path
                    break
            
            if preview_path:
                try:
                    def add_preview():
                        # Create a container for the image
                        box = Gtk.Box()
                        box.set_margin_start(2)
                        box.set_margin_end(2)
                        box.set_margin_top(2)
                        box.set_margin_bottom(2)
                        
                        # Handle GIF animations
                        if preview_path.lower().endswith('.gif'):
                            try:
                                # Load animation
                                animation = GdkPixbuf.PixbufAnimation.new_from_file(preview_path)
                                if animation.is_static_image():
                                    # Handle static GIFs like normal images
                                    pixbuf = animation.get_static_image().scale_simple(
                                        self.preview_width,
                                        self.preview_height,
                                        GdkPixbuf.InterpType.BILINEAR
                                    )
                                    image = Gtk.Image.new_from_pixbuf(pixbuf)
                                else:
                                    # Create an iterator for the animation
                                    iter = animation.get_iter(None)
                                    # Get the first frame for scaling reference
                                    first_frame = iter.get_pixbuf()
                                    # Calculate scaling factors
                                    scale_x = self.preview_width / first_frame.get_width()
                                    scale_y = self.preview_height / first_frame.get_height()
                                    scale = min(scale_x, scale_y)
                                    
                                    # Create a scaled animation
                                    def create_scaled_animation():
                                        frames = []
                                        iter = animation.get_iter(None)
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
                                        return frames
                                    
                                    frames = create_scaled_animation()
                                    
                                    # Create image widget with animation
                                    image = Gtk.Image()
                                    current_frame = 0
                                    
                                    def update_frame():
                                        nonlocal current_frame
                                        image.set_from_pixbuf(frames[current_frame])
                                        current_frame = (current_frame + 1) % len(frames)
                                        return True
                                    
                                    # Update frame every 50ms (20fps)
                                    GLib.timeout_add(50, update_frame)
                            except GLib.Error:
                                # Fallback to static image if animation fails
                                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                                    preview_path,
                                    self.preview_width,
                                    self.preview_height,
                                    True)
                                image = Gtk.Image.new_from_pixbuf(pixbuf)
                        else:
                            # Handle static images
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                                preview_path,
                                self.preview_width,
                                self.preview_height,
                                True)
                            image = Gtk.Image.new_from_pixbuf(pixbuf)
                        
                        box.add(image)
                        box.wallpaper_id = wallpaper_id
                        self.flowbox.add(box)
                        box.show_all()
                        
                        if wallpaper_id == self.engine.current_wallpaper:
                            self.highlight_current_wallpaper(box)
                    
                    GLib.idle_add(add_preview)
                    
                except Exception as e:
                    self.log.error(f"Failed to load preview for {wallpaper_id}: {e}")

        # Clear existing previews
        self.flowbox.foreach(lambda w: w.destroy())
        
        # Load new previews in background
        wallpapers = self.engine.get_wallpaper_list()
        self.status_label.set_text(f"Loading {len(wallpapers)} wallpapers...")
        
        for wallpaper_id in wallpapers:
            thread = threading.Thread(target=load_preview, args=(wallpaper_id,))
            thread.daemon = True
            thread.start()

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

    def on_settings_clicked(self, button):
        """Open settings dialog"""
        dialog = SettingsDialog(self)
        response = dialog.run()
        
        dialog.destroy()  # Destroy dialog first to prevent GTK warnings
        
        if response != Gtk.ResponseType.OK:
            return  # Don't apply settings if cancelled
            
        try:
            # Save settings
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
                'clamping': dialog.clamping_combo.get_active_text()
            }
            
            # Apply settings
            self.apply_settings(settings)
        except Exception as e:
            self.log.error(f"Failed to apply settings: {e}")
    
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
                clamping=settings['clamping']
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