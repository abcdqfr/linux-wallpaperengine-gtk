#!/usr/bin/env python3
"""
Linux Wallpaper Engine GTK Frontend
A standalone GTK interface for linux-wallpaperengine
"""

import logging
import os
import json
import sys
import random
import argparse
import subprocess
import threading
import time
import shutil
import datetime
import pathlib
import typing
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any, Set, Union, Callable

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk

from src.wallpaperengine.machine_opt import ᴘᴍ, ꜱᴍ, ᴜɪ, ᴡᴇ, ɢᴛᴋ, ᴅʟɢ

def ᴍᴀɪɴ():
    # Setup logging with more verbose output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('wallpaper-engine.log'),
            logging.StreamHandler()
        ]
    )
    
    # Parse arguments
    ᴘ = argparse.ArgumentParser(description='Linux Wallpaper Engine GTK Frontend')
    ᴘ.add_argument('--wpe-path', help='Path to linux-wallpaperengine executable')
    ᴘ.add_argument('--fps', type=int, default=60, help='Default FPS')
    ᴘ.add_argument('--volume', type=int, default=100, help='Default volume')
    ᴘ.add_argument('--disable-mouse', action='store_true', help='Disable mouse interaction')
    ᴘ.add_argument('--no-automute', action='store_true', help='Disable auto-muting')
    ᴘ.add_argument('--no-audio-processing', action='store_true', help='Disable audio processing')
    ᴘ.add_argument('--no-fullscreen-pause', action='store_true', help='Disable fullscreen pause')
    ᴘ.add_argument('--scaling', choices=['default', 'center', 'stretch'], default='default', help='Scaling mode')
    ᴘ.add_argument('--clamping', choices=['clamp', 'repeat'], default='clamp', help='Texture clamping mode')
    ᴀ = ᴘ.parse_args()
    
    # Create window
    try:
        ᴡ = ɢᴛᴋ(wpe_path=ᴀ.wpe_path)
        ᴡ.connect("destroy", Gtk.main_quit)
        ᴡ.show_all()
        Gtk.main()
    except Exception as ᴇ:
        logging.error(f"Failed to start: {ᴇ}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    ᴍᴀɪɴ()
