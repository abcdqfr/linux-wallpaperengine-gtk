"""
Linux Wallpaper Engine GTK Frontend
A standalone GTK frontend for linux-wallpaperengine
"""
import logging
import os
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk

class PathManager:
    """Handles path resolution and validation"""
    def __init__(self):
        self.paths = {}  # {category: {path: exists}}
        self.config = os.path.expanduser('~/.config/linux-wallpaperengine-gtk')
        self.logger = logging.getLogger('PathManager')

    def find_path(self, category: str, paths: list[str]) -> Optional[str]:
        """Find first existing path in list"""
        if category not in self.paths:
            self.paths[category] = {}
        for path in paths:
            if path in self.paths[category]:
                return path if self.paths[category][path] else None
            full_path = os.path.expanduser(path)
            exists = os.path.exists(full_path)
            self.paths[category][path] = exists
            if exists:
                self.logger.info(f'Found {category} at: {full_path}')
                return full_path
        return None

class SettingsManager:
    """Manages application settings and persistence"""
    def __init__(self, defaults: dict):
        self.defaults = defaults
        self.current = defaults.copy()
        self.path = os.path.expanduser('~/.config/linux-wallpaperengine-gtk/settings.json')
        self.logger = logging.getLogger('SettingsManager')
        self._load()

    def _load(self) -> None:
        """Load settings from file"""
        try:
            if os.path.exists(self.path):
                with open(self.path, 'r') as f:
                    self.current = json.load(f)
        except Exception as e:
            self.logger.error(f'Load failed: {e}')
            self.current = self.defaults.copy()

    def get(self, key: str) -> Any:
        """Get setting value"""
        return self.current.get(key, self.defaults.get(key))

    def set(self, key: str, value: Any) -> None:
        """Set setting value"""
        self.current[key] = value

    def save(self) -> bool:
        """Save settings to file"""
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'w') as f:
                json.dump(self.current, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f'Save failed: {e}')
            return False

class WallpaperEngine:
    """Core wallpaper engine functionality"""
    def __init__(self, wpe_path=None):
        self.path_manager = PathManager()
        self.logger = logging.getLogger('WallpaperEngine')
        self.display = self._detect_display()
        self.current_wallpaper = None
        self.current_process = None
        self.wpe_path = wpe_path
        if not self.wpe_path:
            self.wpe_path = self.path_manager.find_path('wpe', [
                '~/linux-wallpaperengine/build/linux-wallpaperengine',
                '~/src/linux-wallpaperengine/build/linux-wallpaperengine',
                '/usr/local/bin/linux-wallpaperengine',
                '/usr/bin/linux-wallpaperengine',
                os.path.expanduser('~/bin/linux-wallpaperengine')
            ])
        self.wallpaper_dir = self.path_manager.find_path('wallpapers', [
            '~/.steam/steam/steamapps/workshop/content/431960',
            '~/.steam/debian-installation/steamapps/workshop/content/431960',
            '~/.local/share/Steam/steamapps/workshop/content/431960'
        ])

    def _detect_display(self) -> Optional[str]:
        """Detect primary display"""
        try:
            result = subprocess.run("xrandr | grep -w 'primary'", shell=True, capture_output=True, text=True)
            if result.stdout:
                display = result.stdout.split()[0]
                self.logger.info(f'Found primary: {display}')
                return display
            result = subprocess.run("xrandr | grep -w 'connected'", shell=True, capture_output=True, text=True)
            if result.stdout:
                display = result.stdout.split()[0]
                self.logger.info(f'Using: {display}')
                return display
        except Exception as e:
            self.logger.error(f'Display detection failed: {e}')
        return None

    def get_previous_wallpaper(self) -> Optional[str]:
        """Get previous wallpaper in list"""
        wallpapers = self._get_wallpapers()
        if not wallpapers:
            return None
        try:
            idx = wallpapers.index(self.current_wallpaper)
            return wallpapers[(idx - 1) % len(wallpapers)]
        except ValueError:
            return wallpapers[-1] if wallpapers else None

    def get_next_wallpaper(self) -> Optional[str]:
        """Get next wallpaper in list"""
        wallpapers = self._get_wallpapers()
        if not wallpapers:
            return None
        try:
            idx = wallpapers.index(self.current_wallpaper)
            return wallpapers[(idx + 1) % len(wallpapers)]
        except ValueError:
            return wallpapers[0] if wallpapers else None

    def _get_wallpapers(self) -> List[str]:
        """Get list of available wallpapers"""
        if not self.wallpaper_dir:
            return []
        try:
            wallpapers = [d for d in os.listdir(self.wallpaper_dir) if d.isdigit()]
            self.logger.info(f'Found {len(wallpapers)} wallpapers')
            return sorted(wallpapers)
        except Exception as e:
            self.logger.error(f'Error reading wallpapers: {e}')
            return []

    def run(self, wallpaper_id: str, **options) -> Tuple[bool, Optional[List[str]]]:
        """Run wallpaper engine with specified options"""
        orig_dir = None
        if not all([self.wpe_path, self.display, wallpaper_id]):
            self.logger.error(f'Missing components - wpe: {self.wpe_path}, display: {self.display}, id: {wallpaper_id}')
            return (False, None)
        try:
            self.logger.info('Stopping current...')
            self.stop()
            orig_dir = os.getcwd()
            self.logger.debug(f'Original dir: {orig_dir}')
            work_dir = os.path.dirname(self.wpe_path)
            self.logger.info(f'Changing to: {work_dir}')
            os.chdir(work_dir)
            
            cmd = [self.wpe_path]
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
            cmd.extend(['--screen-root', self.display, wallpaper_id])
            
            self.logger.info(f'Running: {" ".join(map(str, cmd))}')
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL, 
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
                cwd=work_dir
            )
            
            time.sleep(0.1)
            if process.poll() is None:
                self.current_wallpaper = wallpaper_id
                self.current_process = process
                self.logger.info(f'Started PID: {process.pid}')
                return (True, cmd)
            else:
                self.logger.error('Failed to start')
                return (False, None)
        except Exception as e:
            self.logger.error(f'Failed to run: {str(e)}', exc_info=True)
            return (False, None)
        finally:
            if orig_dir:
                self.logger.debug(f'Returning to: {orig_dir}')
                os.chdir(orig_dir)

    def stop(self) -> bool:
        """Stop all running wallpaper processes"""
        try:
            if self.current_process:
                self.current_process.terminate()
                time.sleep(0.1)
                if self.current_process.poll() is None:
                    self.current_process.kill()
                    time.sleep(0.1)
            
            self.logger.info('Stopping processes...')
            while True:
                result = subprocess.run(['pgrep', '-f', f'{self.wpe_path}\\b'], capture_output=True, text=True)
                self.logger.debug(f'pgrep code: {result.returncode}')
                if result.returncode != 0:
                    self.logger.debug('No processes found')
                    break
                    
                pids = result.stdout.strip().split('\n')
                self.logger.debug(f'Found PIDs: {pids}')
                self.logger.info('Sending SIGTERM')
                subprocess.run(['pkill', '-15', '-f', f'{self.wpe_path}\\b'])
                time.sleep(0.1)
                
                check = subprocess.run(['pgrep', '-f', f'{self.wpe_path}\\b'], capture_output=True)
                self.logger.debug(f'After SIGTERM code: {check.returncode}')
                if check.returncode == 0:
                    self.logger.info('Using SIGKILL')
                    subprocess.run(['pkill', '-9', '-f', f'{self.wpe_path}\\b'])
                    self.logger.info('Sent SIGKILL')
                    time.sleep(0.1)
                    
                final = subprocess.run(['pgrep', '-f', f'{self.wpe_path}\\b'], capture_output=True)
                self.logger.debug(f'Final check code: {final.returncode}')
                
            self.current_process = None
            self.current_wallpaper = None
            self.logger.info('All processes stopped')
            time.sleep(0.2)
            return True
        except Exception as e:
            self.logger.error(f'Failed to stop: {e}', exc_info=True)
            return False

class MainWindow(Gtk.Window):
    """Main application window"""
    def __init__(self, wpe_path=None):
        super().__init__(title='Linux Wallpaper Engine')
        self.set_default_size(800, 600)
        
        # Initialize components
        self.engine = WallpaperEngine(wpe_path)
        self.logger = logging.getLogger('GUI')
        self.settings = SettingsManager({
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
        
        self.preview_width = 200
        self.preview_height = 120
        self.preview_thread = None
        self.preview_active = False

        # Build UI
        self.setup_ui()
        self.setup_keyboard_shortcuts()
        self.load_wallpapers()
        
        if not self.validate_state():
            self.show_error('System State Invalid', 
                          'Could not find required components.\n' + 
                          'Please ensure linux-wallpaperengine is installed.')
            raise RuntimeError('Invalid state')

class SettingsDialog(Gtk.Dialog):
    """Settings configuration dialog"""
    def __init__(self, parent: MainWindow, settings: dict):
        super().__init__(title='Settings', parent=parent, flags=0)
        self.parent = parent
        
        # Create notebook for tabbed interface
        notebook = Gtk.Notebook()
        self.get_content_area().pack_start(notebook, True, True, 0)
        
        # Add settings pages
        self.add_general_settings(notebook)
        self.add_display_settings(notebook)
        self.add_performance_settings(notebook)
        self.add_audio_settings(notebook)
        
        # Add dialog buttons
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        self.set_default_size(700, 500)
        self.show_all()

def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    window = MainWindow()
    window.connect('destroy', Gtk.main_quit)
    window.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()