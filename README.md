<p align="center">
  <a href="https://github.com/abcdqfr/linux-wallpaperengine-gtk/blob/main/LICENSE"><img src="https://img.shields.io/github/license/abcdqfr/linux-wallpaperengine-gtk" alt="License" /></a>
  <a href="https://github.com/abcdqfr/linux-wallpaperengine-gtk/releases"><img src="https://img.shields.io/github/v/release/abcdqfr/linux-wallpaperengine-gtk" alt="Release" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python" /></a>
  <a href="https://github.com/abcdqfr/linux-wallpaperengine-gtk"><img src="https://img.shields.io/badge/platform-Linux-lightgrey" alt="Platform" /></a>
  <a href="https://github.com/abcdqfr/linux-wallpaperengine-gtk/stargazers"><img src="https://img.shields.io/github/stars/abcdqfr/linux-wallpaperengine-gtk" alt="Stars" /></a>
  <a href="https://github.com/abcdqfr/linux-wallpaperengine-gtk/network/members"><img src="https://img.shields.io/github/forks/abcdqfr/linux-wallpaperengine-gtk" alt="Forks" /></a>
  <a href="https://github.com/abcdqfr/linux-wallpaperengine-gtk/issues"><img src="https://img.shields.io/github/issues/abcdqfr/linux-wallpaperengine-gtk" alt="Issues" /></a>
</p>

# 🎨 Linux Wallpaper Engine GTK

A beautiful, deterministic GTK frontend for [linux-wallpaperengine](https://github.com/linux-wallpaperengine/engine), designed to work everywhere on Linux.

**Standalone Operation**: Single Python file, no external dependencies. NixOS-style determinism.

## Features

- 🎨 **Beautiful GTK3 Interface**: Intuitive FlowBox-based wallpaper browser
- 🐳 **Containerization Support**: Optional Docker isolation for crash protection (standalone, no external scripts)
- 🛡️ **AMD GPU Workarounds**: Built-in radeonsi driver crash prevention
- 🎯 **Smart Argument Filtering**: Automatically prevents crashes in single-process mode
- ⚙️ **Advanced Settings**: CEF arguments, environment variables, and workarounds
- 📱 **System Tray Integration**: Minimize to tray with AppIndicator3
- 🎵 **Audio Controls**: Volume slider and mute toggle
- 🔄 **Auto-Detection**: Automatically finds wallpapers and backend executable using XDG standards

## Installation

### Quick Start (Users)

**You only need the standalone Python file:**

```bash
# Download just the application
curl -O https://raw.githubusercontent.com/abcdqfr/linux-wallpaperengine-gtk/main/linux-wallpaperengine-gtk.py

# Or using wget
wget https://raw.githubusercontent.com/abcdqfr/linux-wallpaperengine-gtk/main/linux-wallpaperengine-gtk.py

# Make executable
chmod +x linux-wallpaperengine-gtk.py

# Run (will check dependencies and provide installation instructions if needed)
./linux-wallpaperengine-gtk.py
```

**That's it!** The standalone file is all you need. If any dependencies are missing, the application will detect your distribution and provide specific installation commands. All other files in this repository are for developers only.

<details>
<summary><strong>📦 System Dependencies (Auto-Detected)</strong></summary>

The application automatically checks for required dependencies and provides distro-specific installation instructions if anything is missing. Required system packages:

- **Python 3.8+** - Usually pre-installed on modern Linux distributions
- **GTK3/PyGObject** - Python bindings for GTK3 (auto-detected with installation commands)

#### Manual Installation (if needed)

If you prefer to install dependencies manually:

**Ubuntu/Debian/Mint:**

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

**Fedora:**

```bash
sudo dnf install python3-gobject gtk3
```

**Arch Linux:**

```bash
sudo pacman -S python-gobject gtk3
```

**NixOS:**

```bash
nix-env -iA nixos.python3Packages.pygobject3 nixos.gtk3
```

**openSUSE:**

```bash
sudo zypper install python3-gobject gtk3
```

</details>

<details>
<summary><strong>🔧 Developer Setup</strong></summary>

If you're contributing or developing:

```bash
# Clone the full repository
git clone https://github.com/abcdqfr/linux-wallpaperengine-gtk.git
cd linux-wallpaperengine-gtk

# Make executable
chmod +x linux-wallpaperengine-gtk.py

# Run
./linux-wallpaperengine-gtk.py
```

**Note:** Other files (`.gitignore`, `.github/`, `.pre-commit-config.yaml`, `.releaserc.json`) are developer tooling and not needed for end users.

</details>

## Usage

### Basic Usage

1. **Launch the application**

   ```bash
   ./linux-wallpaperengine-gtk.py
   ```

2. **Browse wallpapers** - Use arrow keys or mouse to navigate the FlowBox grid

3. **Select a wallpaper** - Click to launch, or use Enter key

4. **Access settings** - Click the ⚙️ button in the toolbar

<details>
<summary><strong>⚙️ Advanced Features</strong></summary>

#### Containerization

Run wallpapers in Docker for complete isolation (standalone, no external scripts):

1. Enable in Settings > Advanced > Containerization
2. Requires Docker installed and user in `docker` group
3. Automatically detected if available
4. Uses direct `docker run` commands (no external scripts needed)

#### Radeonsi Workarounds

Built-in fixes for AMD GPU crashes:

1. Enable in Settings > Advanced > Radeonsi Workarounds
2. Automatically applied based on detected GPU
3. Individual workarounds can be toggled

#### CEF Arguments

Configure CEF arguments for advanced users:

- **Intel Graphics Fix**: Optimized settings for Intel graphics
- **Debug Mode**: Enable CEF debugging and logging
- **Performance Mode**: Optimize for performance
- **Custom Arguments**: Add your own CEF arguments

</details>

<details>
<summary><strong>🏗️ Architecture</strong></summary>

### Monolithic Design

This project uses a **single-file monolithic structure** optimized for:

- ✅ Agentic coding workflows
- ✅ Simple distribution (one file)
- ✅ Easy maintenance
- ✅ Deterministic behavior
- ✅ Standalone operation (no external files)

### Core Components

- **EnvironmentDetector**: Comprehensive environment detection (distro, compositor, GPU, display)
- **WallpaperEngine**: Core wallpaper management, process lifecycle, containerization
- **WallpaperWindow**: Main GTK UI window with FlowBox, toolbar, status bar
- **SettingsDialog**: Configuration management with Advanced tab
- **WallpaperContextMenu**: Right-click context menu functionality

### Deterministic Approach

The application is designed to work everywhere by:

- Detecting environment (distro, compositor, GPU, display server)
- Using XDG Base Directory Standard for paths
- Graceful degradation when features unavailable
- No hardcoded paths or assumptions
- Standalone container execution (no external scripts)

</details>

<details>
<summary><strong>🔧 Troubleshooting</strong></summary>

### Common Issues

**Wallpaper not launching**

- Check that `linux-wallpaperengine` is installed and in PATH
- Verify display detection: `xrandr` (X11) or `swaymsg -t get_outputs` (Wayland)
- Check logs: `DEBUG=1 ./linux-wallpaperengine-gtk.py`

**CEF crashes**

- Enable Intel Graphics Fix preset in Advanced settings
- Try containerization mode for isolation
- Check GPU driver: `lspci | grep VGA`

**UI not responding**

- Ensure GTK 3.36+ is installed: `pkg-config --modversion gtk+-3.0`
- Check for Wayland compatibility issues
- Try X11 session if on Wayland

**Containerization not working**

- Verify Docker is installed: `docker --version`
- Check user is in docker group: `groups | grep docker`
- Test Docker access: `docker ps`

### Debug Mode

Enable verbose logging:

```bash
DEBUG=1 ./linux-wallpaperengine-gtk.py
```

</details>

<details>
<summary><strong>🗺️ Roadmap & Feature Status</strong></summary>

### Current Status: v1.2.0 (Deterministic Monolith)

#### ✅ Implemented Features

- 🎨 **Beautiful GTK3 Interface**: Intuitive FlowBox-based wallpaper browser
- 🐳 **Containerization Support**: Optional Docker isolation for crash protection (standalone, no external scripts)
- 🛡️ **AMD GPU Workarounds**: Built-in radeonsi driver crash prevention
- 🎯 **Smart Argument Filtering**: Automatically prevents crashes in single-process mode
- ⚙️ **Advanced Settings**: CEF arguments, environment variables, and workarounds
- 📱 **System Tray Integration**: Minimize to tray with AppIndicator3
- 🎵 **Audio Controls**: Volume slider and mute toggle
- 🔄 **Auto-Detection**: Automatically finds wallpapers and backend executable using XDG standards
- ✅ Single-file monolithic structure
- ✅ Standalone containerization (no external scripts)
- ✅ Comprehensive environment detection
- ✅ XDG-based path resolution
- ✅ Radeonsi workarounds
- ✅ Smart argument filtering
- ✅ System tray integration
- ✅ Standalone Docker execution

#### 🚧 Partial/Planned Features

- 🖥️ **Desktop Icon & Menu Entry**: .desktop file for application menu integration _(needs portable path fix)_
- 📋 **Playlist Management**: Create and manage wallpaper playlists _(planned)_

**Note**: The main Features section (top of README) only lists implemented features for clarity. Partial and planned features are tracked here in the Roadmap and in the FEATURES list (`linux-wallpaperengine-gtk.py`).

</details>

<details>
<summary><strong>🤝 Contributing</strong></summary>

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes (keep it monolithic and standalone!)
4. Test on multiple distros/compositors
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Guidelines

- **Keep it monolithic**: Single file structure
- **Keep it standalone**: No external file dependencies
- **Test everywhere**: Try on different distros/compositors
- **Document assumptions**: If you assume something, detect it instead
- **Use XDG standards**: For paths and configuration

</details>

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [linux-wallpaperengine](https://github.com/linux-wallpaperengine/engine) - The core wallpaper engine (maintained by [almamu](https://github.com/almamu))
- GTK community for the excellent UI framework

---

<details>
<summary><strong>📚 Additional Documentation</strong></summary>

### Deterministic Monolith Plan

**Philosophy**: NixOS-Style Determinism in a Single File

**Goal**: One Python file that works on ALL Linux distros, compositors, drivers, setups

**Approach**: Declarative detection, graceful fallbacks, zero assumptions

#### Implementation

The application uses comprehensive environment detection:

- **Distro Detection**: NixOS, Arch, Ubuntu, Fedora, Debian, etc. (via `/etc/os-release`, distro-specific files)
- **Compositor Detection**: Mutter (GNOME), KWin (KDE), Sway, Hyprland, River (via process detection)
- **Display Server Detection**: X11, Wayland, XWayland (via environment variables)
- **GPU Detection**: AMD/RadeonSI, Intel, NVIDIA (via `lspci` and `lsmod`)
- **Path Resolution**: XDG Base Directory Standard, distro-specific conventions, Flatpak/Snap paths
- **Capability Detection**: Docker/Podman availability, GTK version, permissions

#### Key Principles

1. **Detect Everything, Assume Nothing**: All environment aspects are detected upfront
2. **XDG Standards**: Use XDG Base Directory Standard for all paths
3. **Graceful Degradation**: Work even if some features unavailable
4. **Standalone Operation**: No external scripts or files required

</details>

<details>
<summary><strong>🐳 Containerization Details</strong></summary>

### Standalone Container Execution

The application uses direct `docker run` commands - no external scripts needed.

#### Requirements

- Docker or Podman installed
- User in `docker` group (or use `sudo`)
- Base container image (e.g., `ubuntu:22.04`)

#### How It Works

1. Detects Docker/Podman availability
2. Builds `docker run` command with:
   - GPU device access (`--device=/dev/dri`)
   - X11/Wayland display forwarding
   - Environment variables (workarounds, etc.)
   - Resource limits (memory, CPU)
   - Security settings (required for GPU)

3. Executes directly - no wrapper scripts

#### Manual Container Execution

If you need to run manually:

```bash
docker run --rm \
  --device=/dev/dri \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v /path/to/wpe:/path/to/wpe:ro \
  --network=host \
  ubuntu:22.04 \
  /path/to/linux-wallpaperengine [args]
```

</details>

<details>
<summary><strong>🛡️ AMD GPU Workarounds</strong></summary>

### Radeonsi Driver Crash Prevention

The application automatically detects AMD GPUs and applies workarounds to prevent crashes.

#### Automatic Workarounds (AMD RadeonSI)

When AMD GPU is detected, these workarounds are applied by default:

- `MESA_GL_SYNC_TO_VBLANK=1` - Prevents race conditions
- `MESA_GL_VERSION_OVERRIDE=4.5` - Uses stable OpenGL API
- `MESA_GLSL_VERSION_OVERRIDE=450` - Uses stable GLSL version
- `MESA_GLSL_CACHE_DISABLE=1` - Prevents shader cache corruption
- `R600_DEBUG=nosb,notgsi` - Disables aggressive optimizations

#### Manual Application

If you need to apply manually:

```bash
export MESA_GL_SYNC_TO_VBLANK=1
export MESA_GL_VERSION_OVERRIDE=4.5
export MESA_GLSL_VERSION_OVERRIDE=450
export MESA_GLSL_CACHE_DISABLE=1
export R600_DEBUG=nosb,notgsi
./linux-wallpaperengine-gtk.py
```

#### Intel GPU

Minimal workarounds applied:

- `MESA_GL_VERSION_OVERRIDE=4.5`

#### NVIDIA GPU

Usually works fine without workarounds.

</details>

<details>
<summary><strong>🔧 Environment Detection Details</strong></summary>

### Comprehensive Detection

The `EnvironmentDetector` class detects:

#### Distro Detection Methods

1. `/etc/os-release` (systemd standard)
2. `/etc/lsb-release` (Debian/Ubuntu)
3. Distro-specific files:
   - `/etc/arch-release` → Arch
   - `/etc/fedora-release` → Fedora
   - `/etc/nixos/configuration.nix` → NixOS
   - `/etc/debian_version` → Debian
   - etc.

#### Compositor Detection

- **Wayland**: Checks running processes for `mutter`, `kwin`, `sway`, `hyprland`, `river`
- **X11**: Uses `xprop` to detect window manager

#### GPU Detection

- **Method 1**: `lspci -nnk` to detect GPU vendor
- **Method 2**: `lsmod` to detect driver modules (`amdgpu`, `radeon`, `nvidia`, `i915`)

#### Path Resolution

- **Steam**: XDG paths, standard locations, distro-specific, Flatpak, Snap
- **WPE Binary**: PATH, system paths, XDG paths, relative paths, distro-specific

</details>

<details>
<summary><strong>🐛 Known Issues & Solutions</strong></summary>

### Backend Crashes (SIGSEGV)

**Symptom**: Backend crashes with segmentation fault

**Cause**: GPU driver memory corruption (often AMD RadeonSI)

**Solutions**:

1. Enable Radeonsi workarounds (automatic if AMD GPU detected)
2. Use containerization for isolation
3. Update GPU drivers
4. Check `dmesg` for driver errors

### Wayland Compatibility

**Symptom**: Wallpapers don't display on Wayland

**Cause**: Backend requires X11 for display access

**Solutions**:

1. Switch to X11 session (recommended)
2. Use XWayland compatibility mode
3. Check compositor-specific display detection

### Containerization Issues

**Symptom**: Container fails to start or can't access GPU

**Solutions**:

1. Verify Docker is running: `docker ps`
2. Check user in docker group: `groups | grep docker`
3. Test GPU access: `docker run --device=/dev/dri ubuntu:22.04 lspci`
4. Check permissions: May need `sudo` or group membership

</details>

---

**Status**: v1.2.0 - Deterministic Monolith (Standalone Operation)
