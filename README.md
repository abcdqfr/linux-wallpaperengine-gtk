# Wallpaper Engine GTK

A GTK frontend for [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine) that provides a user-friendly interface for managing Steam Workshop wallpapers on Linux. This application makes it easy to browse, preview, and switch between your Wallpaper Engine wallpapers.

![Screenshot placeholder]()

## Overview

This project aims to provide a native GTK interface for linux-wallpaperengine, making it easier for Linux users to enjoy their Wallpaper Engine collection. While linux-wallpaperengine handles the core functionality of running the wallpapers, this frontend focuses on providing a seamless user experience for managing them.

## Features

- 🖼️ Visual wallpaper browser with thumbnails and previews
- 🔄 Easy wallpaper switching (next/previous/random)
- 🎵 Audio controls (volume/mute)
- 🖥️ Multi-monitor support
- ⚙️ Graphical settings management
FUTURE- 🔧 System tray integration with quick controls

## Prerequisites

- [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine) (built and configured)
- Steam Workshop wallpapers (from Wallpaper Engine)
- Python 3.6+
- GTK 3.0

### System Dependencies

	sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0

### On Fedora

	sudo dnf install python3-gobject gtk3

### On Arch Linux

	sudo pacman -S python-gobject gtk3


## Installation

1. Install linux-wallpaperengine first:

		git clone https://github.com/Almamu/linux-wallpaperengine.git
		cd linux-wallpaperengine
		mkdir build && cd build
		cmake ..
		make

2. Install Linux Wallpaper Engine GTK:

### From Source

	git clone https://github.com/abcdqfr/linux-wallpaperengine-gtk.git
	cd linux-wallpaperengine-gtk
	python3 linux-wallpaperengine-gtk.py

## Configuration

On first run, the application will create a configuration file at:

    ~/.config/linux-wallpaperengine-gtk/config.json

Default paths:
  - `~/linux-wallpaperengine/build`
  - `~/.steam/steam/steamapps/workshop/content/431960`
  - `~/.steam/debian-installation/steamapps/workshop/content/431960`
  - `~/.local/share/Steam/steamapps/workshop/content/431960`

You can change these paths in the settings dialog.

## Usage

### Starting the Application

Launch the application by running:

    python3 linux-wallpaperengine-gtk.py

The application will automatically detect linux-wallpaperengine and wallpapers in common locations.

### Basic Controls

- Click any wallpaper preview to apply it
- Use toolbar buttons for:
  - Previous wallpaper (←)
  - Next wallpaper (→)
  - Random wallpaper (🔀)
  - Settings (⚙️)

### Settings

Access settings through the gear icon to configure:
- Linux Wallpaper Engine path
- Wallpaper directory
- Audio/Mouse behavior

### System Tray

The application minimizes to system tray. Right-click the tray icon for quick actions:
- Next/Previous/Random wallpaper
- Show main window
- Exit

## Troubleshooting

### Common Issues

1. **No wallpapers showing:**
   - Check if wallpaper directory is correctly set
   - Ensure you have wallpapers downloaded from Steam Workshop
   - Verify file permissions

2. **Wallpapers not loading:**
   - Verify linux-wallpaperengine path
   - Check if linux-wallpaperengine is properly built
   - Run from terminal to see error messages

3. **Preview images not loading:**
   - Ensure wallpaper directories contain preview files
   - Check file permissions
   - Verify GTK and GDK are properly installed

### Debug Mode

Run with debug logging enabled:

	python3 linux-wallpaperengine-gtk.py --debug

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine) for the core wallpaper engine functionality
- Steam Workshop for wallpaper content

## Related Projects

- [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine) - The core wallpaper engine for Linux
