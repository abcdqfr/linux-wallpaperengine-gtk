# Linux Wallpaper Engine GTK

A GTK frontend for [linux-wallpaperengine](https://github.com/linux-wallpaperengine/engine),
providing an intuitive interface for managing Wallpaper Engine wallpapers on Linux.

## Features
- **Dual Monitor Support**: Apply independent wallpapers to each monitor!
- **Wallpaper Management**: Browse, select, and launch wallpapers with ease
- **Settings Dialog**: Configure wallpaper engine settings and CEF arguments
- **Refresh Functionality**: Reload wallpaper list when new wallpapers are added
- **Professional Development**: Modern Python packaging with `src/` structure and comprehensive testing

## Installation

### Quick Start (Standalone)

Download the standalone file and run:

```bash
# Download the standalone file
wget https://github.com/abcdqfr/linux-wallpaperengine-gtk/linux-wallpaperengine-gtk.py

# Make executable
chmod +x linux-wallpaperengine-gtk.py

# Run
./linux-wallpaperengine-gtk.py
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/abcdqfr/linux-wallpaperengine-gtk.git
cd linux-wallpaperengine-gtk

# Install in development mode
make install

# Run
make run
```

### System Dependencies

#### Ubuntu/Debian/Mint

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

#### Fedora

```bash
sudo dnf install python3-gobject gtk3
```

#### Arch Linux

```bash
sudo pacman -S python-gobject gtk3
```

## Usage

### Basic Usage

1. **Launch the application**

   ```bash
   ./linux-wallpaperengine-gtk.py
   ```

2. **Browse wallpapers** using the arrow keys or mouse

3. **Select a wallpaper** Left click to apply to Primary display, Right to apply to Secondary!!

4. **Access settings** via the settings button (⚙️)

### Advanced Features

#### CEF Arguments

The Advanced tab in settings allows you to configure custom CEF arguments:

- **Intel Graphics Fix**: Optimized settings for Intel graphics cards
- **Debug Mode**: Enable CEF debugging and logging
- **Performance Mode**: Optimize for performance over visual quality
- **Custom Arguments**: Add your own CEF arguments

#### Smart Argument Filtering

The application automatically detects single-process mode and omits problematic arguments like `--scaling` and `--clamping` to prevent crashes.

## Development

### Project Structure

```text
linux-wallpaperengine-gtk/
├── linux-wallpaperengine-gtk.py    # Standalone GTK GUI
├── pyproject.toml                  # Modern Python packaging
├── README.md                       # You are here!
├── LICENSE                         # MIT license
└── Makefile                        # Development commands
```

### Development Commands

```bash
make install      # Install in development mode
make test         # Run tests
make format       # Format code
make lint         # Lint code
make check        # Run all checks
make release      # Prepare release
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/pytest_suite_test.py -v
```

## Troubleshooting

### Common Issues

**Wallpaper not launching**: Check that `linux-wallpaperengine` is installed and accessible in your PATH.

**CEF crashes**: Try the Intel Graphics Fix preset in Advanced settings. *SEE ALSO!:* 'cef_dual_monitor_performance.patch' to enhance the core engine by Almamu, then build again!

**UI not responding**: Ensure GTK 3.36+ is installed on your system.

### Debug Mode

Enable debug logging by setting the `DEBUG` environment variable:

```bash
DEBUG=1 ./linux-wallpaperengine-gtk-standalone.py
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `make check`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
make dev-setup

# Install pre-commit hooks
pre-commit install
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [linux-wallpaperengine by Almamu](https://github.com/almamu/linux-wallpaperengine/engine) - The core of lwpe-gtk, go give them a star!
