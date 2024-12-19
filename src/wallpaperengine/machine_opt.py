"""Machine-optimized components for linux-wallpaperengine-gtk."""

import logging
import os
import json
import subprocess
import threading
import time
import random
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any, Set, Union, Callable

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk

class ᴘᴍ:  # PathManager
    """KEY: Machine-optimized path resolution
    ᴘ: paths dict {category: {path: exists}}
    ᴄ: config path str
    """
    def __init__(ꜱ):
        ꜱ.ᴘ = {}  # paths
        ꜱ.ᴄ = os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
        ꜱ.ʟ = logging.getLogger('PM')
    
    def ꜰ(ꜱ, cat: str, paths: list[str]) -> str:
        """Find first existing path from list
        cat: category for caching
        paths: paths to check
        """
        if cat not in ꜱ.ᴘ:
            ꜱ.ᴘ[cat] = {}
        for ᴘ in paths:
            if ᴘ in ꜱ.ᴘ[cat]:
                return ᴘ if ꜱ.ᴘ[cat][ᴘ] else None
            ꜰᴘ = os.path.expanduser(ᴘ)
            exists = os.path.exists(ꜰᴘ)
            ꜱ.ᴘ[cat][ᴘ] = exists
            if exists:
                ꜱ.ʟ.ɪɴꜰ(f"Found {cat} at: {ꜰᴘ}")
                return ꜰᴘ
        return None
    
    def ᴠ(ꜱ, paths: Dict[str, str]) -> List[str]:
        """Validate multiple paths
        paths: dict of {name: path}
        Returns: list of missing path names
        """
        missing = []
        for ɴ, ᴘ in paths.items():
            if not ᴘ or not os.path.exists(os.path.expanduser(ᴘ)):
                missing.append(ɴ)
        return missing

    def ᴍᴋ(ꜱ, path: str) -> bool:
        """Make directory and parents
        Returns: success bool
        """
        try:
            os.makedirs(os.path.expanduser(path), exist_ok=True)
            return True
        except Exception as ᴇ:
            ꜱ.ʟ.ᴇx(f"Failed to create {path}: {ᴇ}")
            return False

class ꜱᴍ:  # SettingsManager
    """KEY: Machine-optimized settings
    ᴅ: defaults dict
    ᴄ: current dict
    ᴘ: config path
    """
    def __init__(ꜱ, defaults: dict):
        ꜱ.ᴅ = defaults
        ꜱ.ᴄ = defaults.copy()
        ꜱ.ᴘ = os.path.expanduser("~/.config/linux-wallpaperengine-gtk/settings.json")
        ꜱ.ʟ = logging.getLogger('SM')
        ꜱ._ʟ()  # load
    
    def _ʟ(ꜱ) -> None:
        """Load settings"""
        try:
            if os.path.exists(ꜱ.ᴘ):
                ꜱ.ᴄ.update(json.load(open(ꜱ.ᴘ)))
        except Exception as ᴇ:
            ꜱ.ʟ.ᴇx(f"Load failed: {ᴇ}")
    
    def ɢ(ꜱ, ᴋ: str) -> Any:
        """Get setting with default"""
        return ꜱ.ᴄ.get(ᴋ, ꜱ.ᴅ.get(ᴋ))
    
    def ꜱ(ꜱ, ᴋ: str, ᴠ: Any) -> None:
        """Set setting"""
        ꜱ.ᴄ[ᴋ] = ᴠ
    
    def ꜱᴠ(ꜱ) -> bool:
        """Save settings to disk"""
        try:
            os.makedirs(os.path.dirname(ꜱ.ᴘ), exist_ok=True)
            with open(ꜱ.ᴘ, 'w') as ꜰ:
                json.dump(ꜱ.ᴄ, ꜰ, indent=4)
            return True
        except Exception as ᴇ:
            ꜱ.ʟ.ᴇx(f"Save failed: {ᴇ}")
            return False

class ᴜɪ:  # UIHelper
    """KEY: Machine-optimized UI components
    ᴡ: widgets dict
    ꜱ: styles dict
    """
    @staticmethod
    def ᴅ(title: str, parent: Optional[Gtk.Window] = None, msg: str = "") -> None:
        """Display error dialog"""
        ᴅ = Gtk.MessageDialog(
            transient_for=parent,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        if msg:
            ᴅ.format_secondary_text(msg)
        ᴅ.run()
        ᴅ.destroy()
    
    @staticmethod
    def ɢ(container: Gtk.Container, label: str, widget: Gtk.Widget, row: int, col: int = 0) -> None:
        """Grid attach with label"""
        if isinstance(container, Gtk.Grid):
            ʟ = Gtk.Label(label=label + ":", halign=Gtk.Align.END)
            container.attach(ʟ, col, row, 1, 1)
            container.attach(widget, col + 1, row, 1, 1)
    
    @staticmethod
    def ꜱ(min_val: int, max_val: int, step: int = 1) -> Gtk.SpinButton:
        """Create spin button"""
        ᴀ = Gtk.Adjustment(value=min_val, lower=min_val, upper=max_val, step_increment=step)
        return Gtk.SpinButton(adjustment=ᴀ)
    
    @staticmethod
    def ꜱᴄ(min_val: int, max_val: int, step: int = 1) -> Gtk.Scale:
        """Create horizontal scale"""
        ᴀ = Gtk.Adjustment(value=min_val, lower=min_val, upper=max_val, step_increment=step)
        ꜱ = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=ᴀ)
        ꜱ.set_value_pos(Gtk.PositionType.RIGHT)
        return ꜱ

class ᴡᴇ:  # WallpaperEngine
    """KEY: Machine-optimized wallpaper engine
    ᴘ: path manager
    ᴅ: display str
    ᴡ: current wallpaper
    ᴄ: current process
    """
    def __init__(ꜱ, wpe_path=None):
        ꜱ.ᴘ = ᴘᴍ()  # path manager
        ꜱ.ʟ = logging.getLogger('WE')
        ꜱ.ᴅ = ꜱ._ᴅᴅ()  # detect display
        ꜱ.ᴡ = None  # current wallpaper
        ꜱ.ᴄ = None  # current process
        
        # Find paths
        ꜱ.ᴡᴘ = wpe_path or ꜱ.ᴘ.ꜰ('wpe', [
            "~/linux-wallpaperengine/build/linux-wallpaperengine",
            "~/src/linux-wallpaperengine/build/linux-wallpaperengine",
            "/usr/local/bin/linux-wallpaperengine",
            "/usr/bin/linux-wallpaperengine",
            os.path.expanduser("~/bin/linux-wallpaperengine")
        ])
        
        ꜱ.ᴡᴅ = ꜱ.ᴘ.ꜰ('wallpapers', [
            "~/.steam/steam/steamapps/workshop/content/431960",
            "~/.steam/debian-installation/steamapps/workshop/content/431960",
            "~/.local/share/Steam/steamapps/workshop/content/431960"
        ])
    
    def _ᴅᴅ(ꜱ) -> Optional[str]:
        """Detect display"""
        try:
            # Try primary first
            ʀ = subprocess.run("xrandr | grep -w 'primary'", 
                             shell=True, capture_output=True, text=True)
            if ʀ.stdout:
                ᴅ = ʀ.stdout.split()[0]
                ꜱ.ʟ.ɪɴꜰ(f"Found primary: {ᴅ}")
                return ᴅ
            
            # Fall back to first connected
            ʀ = subprocess.run("xrandr | grep -w 'connected'", 
                             shell=True, capture_output=True, text=True)
            if ʀ.stdout:
                ᴅ = ʀ.stdout.split()[0]
                ꜱ.ʟ.ɪɴꜰ(f"Using: {ᴅ}")
                return ᴅ
        except Exception as ᴇ:
            ꜱ.ʟ.ᴇx(f"Display detection failed: {ᴇ}")
        return None
    
    def ɢᴘ(ꜱ) -> Optional[str]:
        """Get previous wallpaper"""
        ᴡꜱ = ꜱ._ɢᴡ()  # get wallpapers
        if not ᴡꜱ:
            return None
        try:
            ɪ = ᴡꜱ.index(ꜱ.ᴡ)
            return ᴡꜱ[(ɪ - 1) % len(ᴡꜱ)]
        except ValueError:
            return ᴡꜱ[-1] if ᴡꜱ else None
    
    def ɢɴ(ꜱ) -> Optional[str]:
        """Get next wallpaper"""
        ᴡꜱ = ꜱ._ɢᴡ()
        if not ᴡꜱ:
            return None
        try:
            ɪ = ᴡꜱ.index(ꜱ.ᴡ)
            return ᴡꜱ[(ɪ + 1) % len(ᴡꜱ)]
        except ValueError:
            return ᴡꜱ[0] if ᴡꜱ else None
    
    def ɢʀ(ꜱ) -> Optional[str]:
        """Get random wallpaper"""
        ᴡꜱ = ꜱ._ɢᴡ()
        return random.choice(ᴡꜱ) if ᴡꜱ else None
    
    def _ɢᴡ(ꜱ) -> List[str]:
        """Get wallpaper list"""
        if not ꜱ.ᴡᴅ:
            return []
        try:
            ᴡꜱ = [ᴅ for ᴅ in os.listdir(ꜱ.ᴡᴅ) if ᴅ.isdigit()]
            ꜱ.ʟ.ɪɴꜰ(f"Found {len(ᴡꜱ)} wallpapers")
            return sorted(ᴡꜱ)
        except Exception as ᴇ:
            ꜱ.ʟ.ᴇx(f"Error reading wallpapers: {ᴇ}")
            return []
    
    def ʀ(ꜱ, wid: str, **opts) -> Tuple[bool, Optional[List[str]]]:
        """Run wallpaper
        wid: wallpaper ID
        opts: command options
        Returns: (success, command)
        """
        if not all([ꜱ.ᴡᴘ, ꜱ.ᴅ, wid]):
            ꜱ.ʟ.ᴇx(f"Missing components - wpe: {ꜱ.ᴡᴘ}, display: {ꜱ.ᴅ}, id: {wid}")
            return False, None
        
        try:
            ꜱ.ʟ.ɪɴꜰ("Stopping current...")
            ꜱ.stop()
            
            # Save current dir
            od = os.getcwd()
            ꜱ.ʟ.ᴅꜰ(f"Original dir: {od}")
            
            # Change to WPE dir
            wd = os.path.dirname(ꜱ.ᴡᴘ)
            ꜱ.ʟ.ɪɴꜰ(f"Changing to: {wd}")
            os.chdir(wd)
            
            # Build command
            cmd = [ꜱ.ᴡᴘ]
            
            # Add options
            if opts.get('fps'):
                cmd.extend(['--fps', str(opts['fps'])])
            if opts.get('mute'):
                cmd.append('--silent')
            if 'volume' in opts:
                cmd.extend(['--volume', str(int(opts['volume']))])
            if opts.get('no_automute'):
                cmd.append('--noautomute')
            if opts.get('no_audio_processing'):
                cmd.append('--no-audio-processing')
            if opts.get('no_fullscreen_pause'):
                cmd.append('--no-fullscreen-pause')
            if opts.get('disable_mouse'):
                cmd.append('--disable-mouse')
            if opts.get('scaling'):
                cmd.extend(['--scaling', opts['scaling']])
            if opts.get('clamping'):
                cmd.extend(['--clamping', opts['clamping']])
            
            # Add display and wallpaper ID
            cmd.extend(['--screen-root', ꜱ.ᴅ, wid])
            
            ꜱ.ʟ.ɪɴꜰ(f"Running: {' '.join(map(str, cmd))}")
            
            # Create process
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
                cwd=wd
            )
            
            # Check if started
            time.sleep(0.1)
            
            if p.poll() is None:  # Running
                ꜱ.ᴡ = wid
                ꜱ.ᴄ = p
                ꜱ.ʟ.ɪɴꜰ(f"Started PID: {p.pid}")
                return True, cmd
            else:
                ꜱ.ʟ.ᴇx("Failed to start")
                return False, None
            
        except Exception as e:
            ꜱ.ʟ.ᴇx(f"Failed to run: {str(e)}", exc_info=True)
            return False, None
            
        finally:
            ꜱ.ʟ.ᴅꜰ(f"Returning to: {od}")
            os.chdir(od)
    
    def stop(ꜱ) -> bool:
        """Stop current wallpaper"""
        try:
            ꜱ.ʟ.ɪɴꜰ("Stopping processes...")
            
            while True:
                r = subprocess.run(['pgrep', '-f', f'{ꜱ.ᴡᴘ}\\b'], 
                                 capture_output=True, text=True)
                ꜱ.ʟ.ᴅꜰ(f"pgrep code: {r.returncode}")
                if r.returncode != 0:
                    ꜱ.ʟ.ᴅꜰ("No processes found")
                    break
                    
                pids = r.stdout.strip().split('\n')
                ꜱ.ʟ.ᴅꜰ(f"Found PIDs: {pids}")
                
                # Try SIGTERM
                ꜱ.ʟ.ɪɴꜰ("Sending SIGTERM")
                subprocess.run(['pkill', '-15', '-f', f'{ꜱ.ᴡᴘ}\\b'])
                time.sleep(0.1)
                
                # Check if still running
                c = subprocess.run(['pgrep', '-f', f'{ꜱ.ᴡᴘ}\\b'], 
                                 capture_output=True)
                ꜱ.ʟ.ᴅꜰ(f"After SIGTERM code: {c.returncode}")
                if c.returncode == 0:
                    ꜱ.ʟ.ɪɴꜰ("Using SIGKILL")
                    subprocess.run(['pkill', '-9', '-f', f'{ꜱ.ᴡᴘ}\\b'])
                    ꜱ.ʟ.ɪɴꜰ("Sent SIGKILL")
                    time.sleep(0.1)
                
                # Verify cleanup
                f = subprocess.run(['pgrep', '-f', f'{ꜱ.ᴡᴘ}\\b'],
                                 capture_output=True)
                ꜱ.ʟ.ᴅꜰ(f"Final check code: {f.returncode}")
            
            ꜱ.ᴄ = None
            ꜱ.ᴡ = None
            ꜱ.ʟ.ɪɴꜰ("All processes stopped")
            time.sleep(0.2)
            return True

        except Exception as e:
            ꜱ.ʟ.ᴇx(f"Failed to stop: {e}", exc_info=True)
            return False

class G(Gtk.Window):  # GTK Window
    """KEY: Machine-optimized GTK window
    e: wallpaper engine
    s: settings manager
    u: UI helper
    """
    def __init__(s, wpe_path=None):
        super().__init__(title="Linux Wallpaper Engine")
        s.set_default_size(800, 600)
        
        # Core components
        s.e = W(wpe_path)  # engine
        s.l = logging.getLogger('GUI')
        
        # Settings
        s.s = S({
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
        })
        
        # UI state
        s.pw = 200  # preview width
        s.ph = 120  # preview height
        s.pt = None  # playlist timeout
        s.pa = False  # playlist active
        
        # Setup UI
        s._ui()
        s._ks()  # keyboard shortcuts
        
        # Load wallpapers
        s.lw()
        
        # Validate
        if not s._v():
            U.d("System State Invalid", s, 
                "Could not find required components.\n" +
                "Please ensure linux-wallpaperengine is installed.")
            raise RuntimeError("Invalid state")

    def _ui(s):
        """Setup UI"""
        # Main container
        s.mb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        s.add(s.mb)
        
        # Toolbar
        s._tb()
        
        # Wallpaper grid
        sc = Gtk.ScrolledWindow()
        s.fb = Gtk.FlowBox()
        s.fb.set_valign(Gtk.Align.START)
        s.fb.set_max_children_per_line(30)
        s.fb.set_selection_mode(Gtk.SelectionMode.SINGLE)
        s.fb.connect("child-activated", s.ow)  # on wallpaper
        s.fb.connect("button-press-event", s.or_)  # on right click
        sc.add(s.fb)
        s.mb.pack_start(sc, True, True, 0)
        
        # Status bar
        s.sb = Gtk.Statusbar()
        s.sb.set_margin_top(0)
        s.sb.set_margin_bottom(2)
        s.cc = s.sb.get_context_id("command")
        s.mb.pack_end(s.sb, False, False, 0)
        
        # Style
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            .current-wallpaper {
                border: 3px solid @selected_bg_color;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _tb(s):
        """Create toolbar"""
        tb = Gtk.Toolbar()
        tb.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        
        # Status
        si = Gtk.ToolItem()
        sb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        s.sl = Gtk.Label(label="Ready")
        s.sl.set_halign(Gtk.Align.START)
        s.sl.set_valign(Gtk.Align.CENTER)
        sb.pack_start(s.sl, True, True, 0)
        
        # Volume
        vb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        s.vs = U.sc(0, 100)
        s.vs.set_size_request(100, -1)
        s.vs.connect("value-changed", s.ov)  # on volume
        vb.pack_start(s.vs, False, False, 0)
        
        sb.pack_start(vb, False, False, 6)
        si.add(sb)
        si.set_expand(True)
        tb.insert(si, -1)
        
        # Preview size
        ps = Gtk.ToolItem()
        pb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        pb.pack_start(Gtk.Label(label="Preview Size:"), False, False, 0)
        
        sc = U.sc(50, 200, 10)
        sc.set_size_request(100, -1)
        sc.set_value(100)
        sc.connect("value-changed", s.op)  # on preview
        pb.pack_start(sc, True, True, 0)
        
        ps.add(pb)
        tb.insert(ps, -1)
        
        # Control buttons
        for icon, tip, cb in [
            ("media-skip-backward-symbolic", "Previous", s.bp),
            ("media-skip-forward-symbolic", "Next", s.bn),
            ("media-playlist-shuffle-symbolic", "Random", s.br),
            ("preferences-system-symbolic", "Settings", s.bs)
        ]:
            b = Gtk.ToolButton()
            b.set_icon_name(icon)
            b.set_tooltip_text(tip)
            b.connect("clicked", cb)
            tb.insert(b, -1)
        
        s.mb.pack_start(tb, False, False, 0)

    def _ks(s):
        """Setup keyboard shortcuts"""
        a = Gtk.AccelGroup()
        s.add_accel_group(a)
        
        # Navigation
        k, m = Gtk.accelerator_parse("Left")
        a.connect(k, m, Gtk.AccelFlags.VISIBLE, lambda *x: s.bp(None))
        
        k, m = Gtk.accelerator_parse("Right")
        a.connect(k, m, Gtk.AccelFlags.VISIBLE, lambda *x: s.bn(None))
        
        # Random
        k, m = Gtk.accelerator_parse("r")
        a.connect(k, m, Gtk.AccelFlags.VISIBLE, lambda *x: s.br(None))
        
        # Settings
        k, m = Gtk.accelerator_parse("s")
        a.connect(k, m, Gtk.AccelFlags.VISIBLE, lambda *x: s.bs(None))

    def _v(s) -> bool:
        """Validate state"""
        if not s.e.wp:
            s.l.error("WPE not found")
            return False
        if not s.e.d:
            s.l.error("No display")
            return False
        if not s.e.wd:
            s.l.error("No wallpapers")
            return False
        return True

    def lw(s) -> None:
        """Load wallpapers"""
        def lp(wid: str) -> None:
            """Load preview"""
            pp = None
            
            # Find preview
            wp = Path(s.e.wd) / wid
            for ext in ['.gif', '.png', '.jpg', '.webp', '.jpeg']:
                p = wp / f'preview{ext}'
                if p.exists():
                    pp = str(p)
                    break
            
            if pp:
                try:
                    def ap() -> None:
                        """Add preview"""
                        b = Gtk.Box()
                        b.set_margin_start(2)
                        b.set_margin_end(2)
                        b.set_margin_top(2)
                        b.set_margin_bottom(2)
                        
                        try:
                            if pp.lower().endswith('.gif'):
                                s._hg(pp, b)  # handle gif
                            else:
                                s._hs(pp, b)  # handle static
                            
                            b.wallpaper_id = wid
                            s.fb.add(b)
                            b.show_all()
                            
                            if wid == s.e.w:
                                s.hw(b)  # highlight
                            
                        except Exception as e:
                            s.l.error(f"Preview failed for {wid}: {e}")
                    
                    GLib.idle_add(ap)
                    
                except Exception as e:
                    s.l.error(f"Load failed for {wid}: {e}")
        
        # Clear existing
        s.fb.foreach(lambda w: w.destroy())
        
        # Load all
        ws = s.e._gw()
        s.sl.set_text(f"Loading {len(ws)} wallpapers...")
        
        for w in ws:
            t = threading.Thread(target=lp, args=(w,))
            t.daemon = True
            t.start()

    def _hg(s, path: str, box: Gtk.Box) -> None:
        """Handle gif preview"""
        a = GdkPixbuf.PixbufAnimation.new_from_file(path)
        
        if a.is_static_image():
            p = a.get_static_image().scale_simple(
                s.pw, s.ph,
                GdkPixbuf.InterpType.BILINEAR
            )
            i = Gtk.Image.new_from_pixbuf(p)
            box.add(i)
            return
        
        # Animated
        it = a.get_iter(None)
        f = it.get_pixbuf()
        sx = s.pw / f.get_width()
        sy = s.ph / f.get_height()
        sc = min(sx, sy)
        
        fs = []
        while True:
            p = it.get_pixbuf()
            nw = int(p.get_width() * sc)
            nh = int(p.get_height() * sc)
            sp = p.scale_simple(
                nw, nh,
                GdkPixbuf.InterpType.BILINEAR
            )
            fs.append(sp)
            if not it.advance():
                break
        
        i = Gtk.Image()
        box.add(i)
        
        def uf() -> bool:
            """Update frame"""
            c = getattr(uf, 'c', 0)
            i.set_from_pixbuf(fs[c])
            uf.c = (c + 1) % len(fs)
            return True
        
        uf.c = 0
        GLib.timeout_add(50, uf)

    def _hs(s, path: str, box: Gtk.Box) -> None:
        """Handle static preview"""
        p = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            path,
            s.pw,
            s.ph,
            True
        )
        i = Gtk.Image.new_from_pixbuf(p)
        box.add(i)

    def hw(s, box: Optional[Gtk.Box] = None) -> None:
        """Highlight wallpaper"""
        for c in s.fb.get_children():
            b = c.get_child()
            b.get_style_context().remove_class('current-wallpaper')
        
        if box:
            box.get_style_context().add_class('current-wallpaper')

    def uw(s, wid: str) -> None:
        """Update current wallpaper"""
        s.sl.set_text(f"Current: {wid}")
        
        for c in s.fb.get_children():
            b = c.get_child()
            if b.wallpaper_id == wid:
                s.hw(b)
                a = c.get_parent().get_parent().get_vadjustment()
                if a:
                    al = c.get_allocation()
                    a.set_value(al.y - (a.get_page_size() / 2))
                break

    def ow(s, fb: Gtk.FlowBox, child: Gtk.FlowBoxChild) -> None:
        """On wallpaper selected"""
        if not s._v():
            s.sl.set_text("System invalid")
            return
        
        wid = child.get_child().wallpaper_id
        s.sl.set_text(f"Loading {wid}...")
        ok, cmd = s.e.r(wid, **s.s.c)
        
        if ok:
            s.uw(wid)
            if cmd:
                s.uc(cmd)
        else:
            s.sl.set_text("Load failed")

    def or_(s, w: Gtk.Widget, e: Gdk.EventButton) -> bool:
        """On right click"""
        if e.button == 3:
            c = s.fb.get_child_at_pos(e.x, e.y)
            if c:
                wid = c.get_child().wallpaper_id
                m = WallpaperContextMenu(s, wid)
                m.show_all()
                m.popup_at_pointer(e)
                return True
        return False

    def bp(s, b: Optional[Gtk.Button]) -> None:
        """Button previous"""
        if wid := s.e.gp():
            ok, cmd = s.e.r(wid, **s.s.c)
            if ok:
                s.uw(wid)
                if cmd:
                    s.uc(cmd)

    def bn(s, b: Optional[Gtk.Button]) -> None:
        """Button next"""
        if wid := s.e.gn():
            ok, cmd = s.e.r(wid, **s.s.c)
            if ok:
                s.uw(wid)
                if cmd:
                    s.uc(cmd)

    def br(s, b: Optional[Gtk.Button]) -> None:
        """Button random"""
        if wid := s.e.gr():
            ok, cmd = s.e.r(wid, **s.s.c)
            if ok:
                s.uw(wid)
                if cmd:
                    s.uc(cmd)

    def bs(s, b: Optional[Gtk.Button]) -> None:
        """Button settings"""
        d = D(s, s.s.c)
        if d.run() == Gtk.ResponseType.OK:
            s.lw()
        d.destroy()

    def ov(s, scale: Gtk.Scale) -> None:
        """On volume changed"""
        v = scale.get_value()
        s.s.s('volume', v)
        
        if s.e.w:
            ok, cmd = s.e.r(s.e.w, **s.s.c)
            if ok and cmd:
                s.uc(cmd)

    def op(s, scale: Gtk.Scale) -> None:
        """On preview scale"""
        p = scale.get_value() / 100.0
        s.pw = int(200 * p)
        s.ph = int(120 * p)
        s.lw()

    def uc(s, cmd: List[str]) -> None:
        """Update command status"""
        s.sb.pop(s.cc)
        s.sb.push(s.cc, f"Last: {' '.join(map(str, cmd))}")

class D(Gtk.Dialog):  # SettingsDialog
    """KEY: Machine-optimized settings dialog
    p: parent window
    s: settings
    """
    def __init__(s, parent: G, settings: dict):
        super().__init__(title="Settings", parent=parent, flags=0)
        s.p = parent
        s.set_default_size(700, 500)
        
        # Create notebook
        s.n = Gtk.Notebook()
        s.get_content_area().pack_start(s.n, True, True, 0)
        
        # Add tabs
        s._gt()  # general
        s._dt()  # directories
        s._pt()  # performance
        s._at()  # audio
        
        # Add buttons
        s.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        s.connect("response", s.on_response)
        s.show_all()
    
    def _gt(s) -> None:
        """Create general tab"""
        g = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        
        # WPE Path
        s.we = Gtk.Entry()
        s.we.set_text(s.p.e.wp or "")
        b = Gtk.Button(label="Browse")
        b.connect("clicked", s.bw)  # browse wpe
        
        U.g(g, "WPE Path", s.we, 0)
        g.attach(b, 2, 0, 1, 1)
        
        # Add to notebook
        s.n.append_page(g, Gtk.Label(label="General"))
    
    def _dt(s) -> None:
        """Create directories tab"""
        g = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        
        # Directory list
        s.ds = Gtk.ListStore(bool, str, int, int, int, str)
        s.dv = Gtk.TreeView(model=s.ds)
        
        # Columns
        cols = [
            ("Enabled", 0, True),
            ("Directory", 1, True),
            ("Total", 2, False),
            ("Blacklisted", 3, False),
            ("Active", 4, False),
            ("Last Scan", 5, False)
        ]
        
        for t, i, e in cols:
            if i == 0:
                r = Gtk.CellRendererToggle()
                r.connect("toggled", s.dt)  # directory toggle
                c = Gtk.TreeViewColumn(t, r, active=0)
            else:
                r = Gtk.CellRendererText()
                c = Gtk.TreeViewColumn(t, r, text=i)
                c.set_expand(e)
            
            s.dv.append_column(c)
        
        # Scrolled window
        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sc.set_size_request(-1, 200)
        sc.add(s.dv)
        
        g.attach(sc, 0, 0, 3, 1)
        
        # Buttons
        bb = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        bb.set_layout(Gtk.ButtonBoxStyle.START)
        bb.set_spacing(6)
        
        for l, cb in [
            ("Add Directory", s.ad),
            ("Remove Directory", s.rd),
            ("Scan All", s.sa)
        ]:
            b = Gtk.Button(label=l)
            b.connect("clicked", cb)
            bb.add(b)
        
        g.attach(bb, 0, 1, 3, 1)
        
        # Add to notebook
        s.n.append_page(g, Gtk.Label(label="Directories"))
        
        # Populate
        s._pd()
    
    def _pt(s) -> None:
        """Create performance tab"""
        g = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        
        # FPS
        s.fs = U.s(1, 240)
        s.fs.set_value(s.p.s.g('fps'))
        U.g(g, "Default FPS", s.fs, 0)
        
        # Priority
        s.pc = Gtk.ComboBoxText()
        for p in ["Low", "Normal", "High"]:
            s.pc.append_text(p)
        s.pc.set_active(1)
        U.g(g, "Process Priority", s.pc, 1)
        
        # Add to notebook
        s.n.append_page(g, Gtk.Label(label="Performance"))
    
    def _at(s) -> None:
        """Create audio tab"""
        g = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        
        # Volume
        s.vs = U.sc(0, 100)
        s.vs.set_value(s.p.s.g('volume'))
        U.g(g, "Default Volume", s.vs, 0)
        
        # Switches
        sws = [
            ("Keep Playing When Other Apps Play Sound", "no_automute"),
            ("Disable Audio Effects", "no_audio_processing")
        ]
        
        for i, (l, k) in enumerate(sws, start=1):
            sw = Gtk.Switch()
            sw.set_active(s.p.s.g(k))
            setattr(s, f"{k}_switch", sw)
            U.g(g, l, sw, i)
        
        # Add to notebook
        s.n.append_page(g, Gtk.Label(label="Audio"))
    
    def _pd(s) -> None:
        """Populate directory list"""
        s.ds.clear()
        for p, i in s.p.dm.directories.items():
            st = s.p.dm.get_directory_stats(p)
            s.ds.append([
                i['enabled'],
                p,
                st['total_count'],
                st['blacklisted_count'],
                st['active_count'],
                st['last_scan'].split('T')[0] if st.get('last_scan') else 'Never'
            ])
    
    def dt(s, cell: Gtk.CellRendererToggle, path: str) -> None:
        """Directory toggle"""
        it = s.ds.get_iter(path)
        en = not s.ds[it][0]
        dp = s.ds[it][1]
        
        s.ds[it][0] = en
        s.p.dm.toggle_directory(dp, en)
    
    def bw(s, button: Gtk.Button) -> None:
        """Browse WPE"""
        d = Gtk.FileChooserDialog(
            title="Select WPE Executable",
            parent=s,
            action=Gtk.FileChooserAction.OPEN
        )
        d.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        if d.run() == Gtk.ResponseType.OK:
            s.we.set_text(d.get_filename())
        d.destroy()
    
    def ad(s, button: Gtk.Button) -> None:
        """Add directory"""
        d = Gtk.FileChooserDialog(
            title="Select Directory",
            parent=s,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        d.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        if d.run() == Gtk.ResponseType.OK:
            s.p.dm.add_scan_path(d.get_filename())
            s._pd()
        d.destroy()
    
    def rd(s, button: Gtk.Button) -> None:
        """Remove directory"""
        sel = s.dv.get_selection()
        m, it = sel.get_selected()
        if it:
            p = m[it][1]
            c = Gtk.MessageDialog(
                transient_for=s,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Remove directory {p}?"
            )
            if c.run() == Gtk.ResponseType.YES:
                s.p.dm.remove_scan_path(p)
                s._pd()
            c.destroy()
    
    def sa(s, button: Gtk.Button) -> None:
        """Scan all"""
        s.p.dm.rescan_all()
        s._pd()
    
    def on_response(s, dialog: Gtk.Dialog, response: int) -> None:
        """Handle response"""
        if response == Gtk.ResponseType.OK:
            # Update settings
            s.p.s.c.update({
                'fps': s.fs.get_value_as_int(),
                'volume': int(s.vs.get_value()),
                'no_automute': s.no_automute_switch.get_active(),
                'no_audio_processing': s.no_audio_processing_switch.get_active(),
                'process_priority': s.pc.get_active_text()
            })
            
            # Update WPE path
            wp = s.we.get_text()
            if wp != s.p.e.wp:
                s.p.e.wp = wp
            
            # Save
            s.p.s.save()