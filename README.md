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
- 🔧 System tray integration with quick controls

## Prerequisites

- [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine) (built and configured)
- Steam Workshop wallpapers (from Wallpaper Engine)
- Python 3.6+
- GTK 3.0

### System Dependencies

bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0

### On Fedora

bash
sudo dnf install python3-gobject gtk3

### On Arch Linux

bash
sudo pacman -S python-gobject gtk3


## Installation

1. Install linux-wallpaperengine first:

bash
git clone https://github.com/Almamu/linux-wallpaperengine.git
cd linux-wallpaperengine
mkdir build && cd build
cmake ..
make



2. Install Linux Wallpaper Engine GTK:

### From PyPI (Recommended)


bash
pip install linux-wallpaperengine-gtk

### From Source

bash
git clone https://github.com/abcdqfr/linux-wallpaperengine-gtk.git
cd linux-wallpaperengine-gtk
pip install -e .

## Configuration

On first run, the application will create a configuration file at:

bash
~/.config/linux-wallpaperengine-gtk/config.json


Default paths:
- Linux Wallpaper Engine: `~/linux-wallpaperengine/build`
- Wallpapers: `~/.steam/debian-installation/steamapps/workshop/content/431960`

You can change these paths in the settings dialog.

## Usage

### Starting the Application

Launch from your applications menu or run:

bash
linux-wallpaperengine-gtk


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
- Volume level
- Audio muting

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

Run with debug logging:

bash
LINUX_WPE_DEBUG=1 linux-wallpaperengine-gtk



## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine) for the core wallpaper engine functionality
- Steam Workshop for wallpaper content

## Related Projects

- [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine) - The core wallpaper engine for Linux
