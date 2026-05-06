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

A beautiful, deterministic GTK frontend for [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine), designed to work everywhere on Linux.

**GTK frontend**: The UI is a single Python file with no extra Python packages beyond PyGObject/GTK. **Playback requires** the separate `linux-wallpaperengine` **binary** (the upstream C++ engine). **Clone this repo with submodules** to vendor upstream source under `upstream/linux-wallpaperengine`, then build it—see [Clone and build the full stack](#clone-and-build-the-full-stack-gtk--upstream-engine).

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

**That's it for the GUI file.** If any GTK/Python dependencies are missing, the application will suggest distro packages.

> **Wallpaper engine binary:** Downloading only `linux-wallpaperengine-gtk.py` does **not** install the C++ backend. You must install or build [`linux-wallpaperengine`](https://github.com/Almamu/linux-wallpaperengine) ([Arch AUR](https://aur.archlinux.org/), distro packages where available, or **build from source**—including from the submodule path [`upstream/linux-wallpaperengine`](#clone-and-build-the-full-stack-gtk--upstream-engine) after a recursive clone).

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

```bash
git clone --recurse-submodules https://github.com/abcdqfr/linux-wallpaperengine-gtk.git
cd linux-wallpaperengine-gtk

chmod +x linux-wallpaperengine-gtk.py

# Build upstream linux-wallpaperengine (required for playback); see section below
# Then run:
./linux-wallpaperengine-gtk.py
```

If you cloned **without** `--recurse-submodules`, fetch everything with:

```bash
git submodule update --init --recursive
```

**Note:** Other files (`.gitignore`, `.github/`, `.pre-commit-config.yaml`, `.releaserc.json`) are developer tooling; end users who only `curl` the `.py` file do not need them.

</details>

## Clone and build the full stack (GTK + upstream engine)

This repository vendors **[linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine)** as a Git submodule at **`upstream/linux-wallpaperengine`**.

Upstream ships **nested submodules** (CEF build helpers, glslang, `nlohmann/json`, etc.). You **must** initialize submodules **recursively** or CMake fails with missing sources.

**Do not use a shallow clone** (`git clone --depth 1 …`) for this workflow unless you know how to deepen history for submodules; shallow parents often break submodule checkouts.

### 1. Clone and sync submodules

```bash
git clone --recurse-submodules https://github.com/abcdqfr/linux-wallpaperengine-gtk.git
cd linux-wallpaperengine-gtk
```

If the repo was cloned without submodules:

```bash
git submodule update --init --recursive
```

Ensure nested checkouts finished (no leading `-` in status):

```bash
cd upstream/linux-wallpaperengine
git submodule status   # every line should start with a space or +, not -
cd ../..
```

If `git submodule update` stops with **`Unable to find current revision in submodule path 'src/External/json'`** (or the `json` directory is empty), reset that submodule and retry (tested recovery path):

```bash
cd upstream/linux-wallpaperengine
git submodule deinit -f src/External/json
rm -rf src/External/json .git/modules/src/External/json
git submodule update --init --recursive
cd ../..
```

### 2. Install build dependencies

Install the compiler stack **before** CMake. Copy the block for your distro from upstream (maintained there):

[Almamu/linux-wallpaperengine — README (system packages)](https://github.com/Almamu/linux-wallpaperengine/blob/main/README.md)

**Ubuntu 24.04** (reference — run the exact `apt-get install …` line from upstream; names track Ubuntu):

```bash
sudo apt-get update
sudo apt-get install build-essential cmake libxrandr-dev libxinerama-dev libxcursor-dev \
  libxi-dev libgl-dev libglew-dev freeglut3-dev libsdl2-dev liblz4-dev libavcodec-dev \
  libavformat-dev libavutil-dev libswscale-dev libxxf86vm-dev libglm-dev libglfw3-dev \
  libmpv-dev mpv libmpv2 libpulse-dev libpulse0 libfftw3-dev
```

**Debian / other:** use the same package names where available, or install the closest `-dev` equivalents (you need **OpenGL, GLEW, GLFW, GLUT, GLM, SDL2, FFmpeg, LZ4, PulseAudio, FFTW, MPV**, and X11/Wayland headers — CMake will error with the first missing piece).

### 3. Configure and compile the engine

**Network:** the first successful `cmake ..` run **downloads Chromium Embedded Framework (CEF)** into `upstream/linux-wallpaperengine/build/cef/` (large download).

```bash
cd upstream/linux-wallpaperengine
mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . -j"$(nproc)"
```

The `linux-wallpaperengine` binary is **`upstream/linux-wallpaperengine/build/output/linux-wallpaperengine`** (CMake sets the runtime output directory to `output/` inside `build/`).

Sanity check:

```bash
./output/linux-wallpaperengine --help
```

### 4. Run the GTK frontend with that binary

From the **GTK repository root** (`linux-wallpaperengine-gtk/`, next to `linux-wallpaperengine-gtk.py`):

```bash
chmod +x linux-wallpaperengine-gtk.py
export PATH="$PWD/upstream/linux-wallpaperengine/build/output:$PATH"
command -v linux-wallpaperengine   # should print .../build/output/linux-wallpaperengine
./linux-wallpaperengine-gtk.py
```

The log line **`Resolved WPE path: …/linux-wallpaperengine`** confirms the UI found the backend.

**Alternative:** leave `PATH` alone and set **Settings → Paths → Wallpaper Engine Path** to the absolute path of `build/output/linux-wallpaperengine`.

### 5. Optional: Applications menu entry

Use **Settings → Paths → Install menu shortcut…**, or:

```bash
./linux-wallpaperengine-gtk.py --install-desktop
```

## Usage

### Basic Usage

1. **Launch the application** (from a full-stack build, export `PATH` as in [§4](#4-run-the-gtk-frontend-with-that-binary) or configure the engine path in Settings)

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

- 🖥️ **Desktop Icon & Menu Entry**: Freedesktop launcher via Settings or `--install-desktop`
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
- **Keep it standalone for distribution**: The downloadable `.py` stays self-contained; **git clones** may bundle upstream via submodules (see [Clone and build the full stack](#clone-and-build-the-full-stack-gtk--upstream-engine))
- **Test everywhere**: Try on different distros/compositors
- **Document assumptions**: If you assume something, detect it instead
- **Use XDG standards**: For paths and configuration

</details>

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine) — upstream wallpaper engine ([almamu](https://github.com/almamu))
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
