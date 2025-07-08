# Linux Wallpaper Engine GTK

A professional GTK frontend for [linux-wallpaperengine](https://github.com/linux-wallpaperengine/engine),
providing an intuitive interface for managing animated wallpapers on Linux.

## Features

- **Advanced CEF Arguments**: Custom CEF arguments with presets for Intel Graphics Fix, Debug Mode, and Performance Mode
- **Smart Argument Filtering**: Automatically omits problematic arguments in single-process mode
- **Wallpaper Management**: Browse, select, and launch wallpapers with ease
- **Settings Dialog**: Configure wallpaper engine settings and CEF arguments
- **Refresh Functionality**: Reload wallpaper list when new wallpapers are added
- **Professional Development**: Modern Python packaging with `src/` structure and comprehensive testing

## Installation

### Quick Start (Standalone)

Download the standalone file and run:

```bash
# Download the standalone file
wget https://github.com/abcdqfr/linux-wallpaperengine-gtk/releases/latest/download/linux-wallpaperengine-gtk-standalone.py

# Make executable
chmod +x linux-wallpaperengine-gtk-standalone.py

# Run
./linux-wallpaperengine-gtk-standalone.py
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
   ./linux-wallpaperengine-gtk-standalone.py
   ```

2. **Browse wallpapers** using the arrow keys or mouse

3. **Select a wallpaper** to launch it

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
├── src/wallpaperengine/     # Source code modules
├── tests/                   # Test suite
├── scripts/                 # Build scripts
├── pyproject.toml          # Modern Python packaging
└── Makefile                # Development commands
```

### Development Commands

```bash
make install      # Install in development mode
make test         # Run tests
make format       # Format code
make lint         # Lint code
make check        # Run all checks
make monolith     # Build standalone file
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

## Architecture

### Core Components

- **WallpaperEngine**: Core wallpaper management and CEF integration
- **WallpaperWindow**: Main GTK UI window and event handling
- **SettingsDialog**: Configuration management and CEF arguments
- **WallpaperContextMenu**: Right-click context menu functionality

### Professional Workflow

The project uses a **round-trip refactoring system**:

1. **Development**: Clean `src/` structure with modern tooling
2. **Distribution**: Standalone monolith for end users
3. **Build System**: Automated conversion between modes

This provides the best of both worlds: professional development experience and simple distribution.

## Troubleshooting

### Common Issues

**Wallpaper not launching**: Check that `linux-wallpaperengine` is installed and accessible in your PATH.

**CEF crashes**: Try the Intel Graphics Fix preset in Advanced settings.

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

- [linux-wallpaperengine](https://github.com/linux-wallpaperengine/engine) - The core wallpaper engine
- [almamu](https://github.com/almamu) - Original GTK implementation inspiration
- GTK community for the excellent UI framework
