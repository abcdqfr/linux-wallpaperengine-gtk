#!/usr/bin/env python3
"""
Linux Wallpaper Engine GTK Frontend.

A standalone GTK interface for linux-wallpaperengine.
"""

import gi

# Require all GTK3 components before importing
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("GLib", "2.0")

import argparse
import json
import logging
import os
import random
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time

from wallpaper_process_probe import pid_exists as _pid_exists
from wallpaper_process_probe import wallpaper_subprocess_running

from gi.repository import Gdk, GdkPixbuf, GLib, Gtk

# Try to import AppIndicator3 for better tray integration (optional)
try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3

    HAS_APP_INDICATOR = True
except (ImportError, ValueError):
    HAS_APP_INDICATOR = False


def install_desktop_entry():
    """
    Install a Freedesktop .desktop file so GNOME, KDE, and other menus list this app.

    Uses absolute paths (via realpath) so the launcher keeps working if the working
    directory changes.

    Returns:
        tuple: ``(success, desktop_file_path_or_error_message)``
    """
    script = os.path.realpath(__file__)
    interpreter = os.path.realpath(sys.executable)

    def _desktop_quote(path: str) -> str:
        if path == "":
            return '""'
        if any(c in path for c in " \t\n\"'\\"):
            return '"' + path.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return path

    exec_field = f"{_desktop_quote(interpreter)} {_desktop_quote(script)}"

    data_home = os.environ.get(
        "XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share")
    )
    apps_dir = os.path.join(data_home, "applications")
    desktop_path = os.path.join(apps_dir, "linux-wallpaperengine-gtk.desktop")

    desktop_body = (
        "[Desktop Entry]\n"
        "Version=1.5\n"
        "Type=Application\n"
        "Name=Linux Wallpaper Engine\n"
        "GenericName=Wallpaper Browser\n"
        "Comment=GTK frontend for linux-wallpaperengine (Wallpaper Engine workshop)\n"
        f"Exec={exec_field}\n"
        "TryExec={try_exe}\n"
        "Icon=preferences-desktop-wallpaper\n"
        "Terminal=false\n"
        "Categories=Graphics;GTK;\n"
        "Keywords=wallpaper;steam;wallpaperengine;gtk;\n"
        "StartupNotify=true\n"
    ).format(try_exe=_desktop_quote(interpreter))

    try:
        os.makedirs(apps_dir, mode=0o755, exist_ok=True)
        with open(desktop_path, "w", encoding="utf-8") as f:
            f.write(desktop_body)
        os.chmod(desktop_path, 0o644)
    except OSError as e:
        return False, str(e)

    for argv in (
        ["update-desktop-database", apps_dir],
        ["update-desktop-database", data_home],
    ):
        try:
            subprocess.run(argv, capture_output=True, timeout=10, check=False)
        except (OSError, subprocess.SubprocessError):
            pass

    return True, desktop_path


def check_dependencies():
    """
    Check for required dependencies and provide helpful error messages.

    Returns:
        tuple: (success: bool, error_message: str or None)

    References:
        - Python argparse: https://docs.python.org/3/library/argparse.html
        - GTK3 Python bindings: https://pygobject.readthedocs.io/
    """
    missing = []
    distro_info = {}

    # Try to detect distro for helpful error messages
    try:
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro_info["id"] = line.split("=", 1)[1].strip().strip('"')
                    elif line.startswith("ID_LIKE="):
                        distro_info["id_like"] = line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass

    # Check Python version
    if sys.version_info < (3, 8):
        missing.append(
            "Python 3.8+ (current: {}.{})".format(sys.version_info.major, sys.version_info.minor)
        )

    # Check GTK3/PyGObject
    try:
        import gi  # noqa: F401

        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
        gi.require_version("GdkPixbuf", "2.0")
        gi.require_version("GLib", "2.0")
        # Test import to verify bindings are available
        from gi.repository import Gdk, GdkPixbuf, GLib, Gtk  # noqa: F401
    except (ImportError, ValueError):
        missing.append("GTK3/PyGObject bindings")

        # Provide distro-specific installation instructions
        install_cmd = None
        distro_id = distro_info.get("id", "").lower()
        id_like = distro_info.get("id_like", "").lower()

        if distro_id in ["ubuntu", "debian", "linuxmint"] or "debian" in id_like:
            install_cmd = "sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0"
        elif distro_id in ["fedora", "rhel", "centos"] or "fedora" in id_like:
            install_cmd = "sudo dnf install python3-gobject gtk3"
        elif distro_id in ["arch", "manjaro", "endeavouros"] or "arch" in id_like:
            install_cmd = "sudo pacman -S python-gobject gtk3"
        elif distro_id == "nixos":
            install_cmd = "nix-env -iA nixos.python3Packages.pygobject3 nixos.gtk3"
        elif distro_id in ["opensuse", "sles"] or "suse" in id_like:
            install_cmd = "sudo zypper install python3-gobject gtk3"
        else:
            install_cmd = "Install python3-gi and gtk3 via your package manager"

        error_msg = f"""
❌ Missing Required Dependencies

The following dependencies are missing:
  • {missing[0]}

Installation Instructions:
  {install_cmd}

For other distributions, install:
  • python3-gi (or python3-gobject)
  • python3-gi-cairo (optional, for better rendering)
  • gir1.2-gtk-3.0 (GTK3 introspection data)

See README.md for complete installation instructions:
  https://github.com/abcdqfr/linux-wallpaperengine-gtk#installation
"""
        return False, error_msg

    return True, None


# Steam Workshop (Wallpaper Engine) — GUI wraps Valve SteamCMD; auth is their stack.
STEAM_WALLPAPER_ENGINE_APP_ID = "431960"
_STEAMCMD_INSTALL_DIR = os.path.join(os.path.expanduser("~"), "steamcmd-local")
_STEAMCMD_URL = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"


def find_steamcmd():
    """Return an executable steamcmd path, or None."""
    for c in (
        os.path.join(_STEAMCMD_INSTALL_DIR, "steamcmd.sh"),
        shutil.which("steamcmd.sh"),
        shutil.which("steamcmd"),
    ):
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    sh = os.path.join(_STEAMCMD_INSTALL_DIR, "steamcmd.sh")
    if os.path.isfile(sh) and os.access(sh, os.R_OK):
        return sh
    return None


def ensure_steamcmd_installed():
    """
    Download official SteamCMD into ~/steamcmd-local. Returns path to steamcmd.sh or None.
    """
    try:
        os.makedirs(_STEAMCMD_INSTALL_DIR, mode=0o755, exist_ok=True)
        curl = subprocess.Popen(
            ["curl", "-fsSL", _STEAMCMD_URL],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        try:
            subprocess.run(
                ["tar", "-C", _STEAMCMD_INSTALL_DIR, "-zx"],
                stdin=curl.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=120,
                check=True,
            )
        finally:
            curl.stdout.close()
            curl.wait(timeout=30)
        exe = os.path.join(_STEAMCMD_INSTALL_DIR, "steamcmd.sh")
        if os.path.isfile(exe):
            os.chmod(exe, 0o755)
            return exe
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def workshop_item_local_status(wallpaper_root, item_id):
    """
    Check project.json main asset exists on disk. Returns (ok: bool, message: str).

    Be conservative about sidecar assumptions: do NOT treat `scene.json` as mandatory
    unless `project.json` references it somewhere. Many Workshop items are video-only
    and never ship a scene file.
    """
    folder = os.path.join(wallpaper_root or "", str(item_id).strip())
    pj = os.path.join(folder, "project.json")
    if not os.path.isdir(folder):
        return False, f"Workshop folder missing:\n{folder}"
    if not os.path.isfile(pj):
        return False, f"No project.json in:\n{folder}"
    try:
        with open(pj, encoding="utf-8") as f:
            meta = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return False, f"Cannot read project.json: {e}"
    fname = meta.get("file")
    if not fname:
        return False, "project.json has no top-level file entry."
    path = os.path.join(folder, fname)
    if os.path.isfile(path):
        referenced_scene_paths = set()

        def _walk(x):
            if isinstance(x, dict):
                for v in x.values():
                    _walk(v)
                return
            if isinstance(x, list):
                for v in x:
                    _walk(v)
                return
            if isinstance(x, str):
                s = x.strip()
                s = s.lstrip("./")
                if s.lower().endswith("scene.json"):
                    referenced_scene_paths.add(s)

        _walk(meta)

        missing = []
        for rel in sorted(referenced_scene_paths):
            candidate = os.path.join(folder, rel)
            if not os.path.isfile(candidate):
                missing.append(candidate)

        if missing:
            return (
                False,
                "Main asset present, but project.json references missing scene files:\n"
                + "\n".join(missing)
                + "\n\nIf Steam never downloads these files, the item may simply not include them "
                "(broken upload or removed content). Try SteamCMD repair; if it persists, "
                "treat this wallpaper as incomplete and skip it.",
            )

        ok_msg = f"OK — asset present:\n{path}"
        if not referenced_scene_paths and not os.path.isfile(os.path.join(folder, "scene.json")):
            ok_msg += (
                "\n\nNote: no scene.json referenced by project.json (common for video wallpapers)."
            )
        return True, ok_msg

    return False, f'Missing main asset file:\n{path}\n(expected from project.json "file")'


def steamcmd_sidecar_paths():
    """Paths where the SteamCMD wrapper leaves exit code and optional typescript transcript."""
    cfg = os.path.expanduser("~/.config/linux-wallpaperengine-gtk")
    return (
        cfg,
        os.path.join(cfg, "last-steamcmd-typescript.txt"),
        os.path.join(cfg, "last-steamcmd.exit"),
    )


def _bash_script_steamcmd_terminal(steamcmd_exe, username, item_id):
    """
    Bash driver for SteamCMD in a real terminal.

    Important: do NOT use exec(1) on steamcmd — it replaces the shell, so the final read never
    runs and the terminal vanishes before you can see errors.

    When util-linux script(1) exists, wrap SteamCMD so output is saved to a typescript file the
    GUI can show later; otherwise run steamcmd directly but still pause at the end.
    """
    cfg, transcript, exit_f = steamcmd_sidecar_paths()
    steam_cmd = (
        f"{shlex.quote(steamcmd_exe)} +@ShutdownOnFailedCommand 1 "
        f"+login {shlex.quote(username)} "
        f"+workshop_download_item {STEAM_WALLPAPER_ENGINE_APP_ID} {shlex.quote(str(item_id))} +quit"
    )
    return f"""set +e
mkdir -p {shlex.quote(cfg)}
T={shlex.quote(transcript)}
E={shlex.quote(exit_f)}
CMD={shlex.quote(steam_cmd)}
if command -v script >/dev/null 2>&1; then
  script -q -e -c "$CMD" "$T"
else
  bash -c "$CMD"
fi
ec=$?
printf %s "$ec" > "$E" 2>/dev/null || true
echo ""
echo "SteamCMD exit code: $ec"
echo "Transcript file (if util-linux script was used): $T"
echo "Exit code file: $E"
read -rp "Press Enter to close…" _
"""


def launch_steamcmd_workshop_in_terminal(steamcmd_exe, username, item_id):
    """
    Start SteamCMD inside a real terminal emulator. Login/password/Steam Guard are handled
    only by Valve's SteamCMD in that TTY — this process never reads or injects credentials.
    Uses +login USER without a password on the command line so SteamCMD prompts interactively.
    """
    inner = _bash_script_steamcmd_terminal(steamcmd_exe, username, item_id)
    for argv in (
        ["gnome-terminal", "--", "bash", "-lc", inner],
        ["konsole", "-e", "bash", "-lc", inner],
        ["x-terminal-emulator", "-e", f"bash -lc {shlex.quote(inner)}"],
    ):
        try:
            subprocess.Popen(argv, start_new_session=True)
            return True
        except OSError:
            continue
    return False


class SteamWorkshopDialog(Gtk.Dialog):
    """Verify local Workshop files and optionally refresh via SteamCMD (Valve)."""

    def __init__(self, parent, preset_item_id=None):
        super().__init__(
            title="Steam Workshop",
            transient_for=parent,
            modal=True,
            destroy_with_parent=True,
        )
        self.main_window = parent
        self.set_default_size(560, 440)
        self.add_buttons("_Close", Gtk.ResponseType.CLOSE)

        grid = Gtk.Grid(row_spacing=8, column_spacing=10, margin=12)
        grid.set_hexpand(True)

        blurb = Gtk.Label(
            xalign=0,
            wrap=True,
            justify=Gtk.Justification.LEFT,
            selectable=False,
        )
        blurb.set_markup(
            "<small>Verify Workshop folders on disk, install Valve SteamCMD here if needed, "
            "or open SteamCMD in a <b>real terminal</b>. Login, password, Steam Guard, and "
            "download failures are handled only by SteamCMD in that terminal — not by this GUI.</small>"
        )
        grid.attach(blurb, 0, 0, 3, 1)

        grid.attach(Gtk.Label(label="Workshop item ID:", halign=Gtk.Align.END), 0, 1, 1, 1)
        self.item_entry = Gtk.Entry()
        self.item_entry.set_placeholder_text("e.g. 2875861661")
        wid = preset_item_id or getattr(parent.engine, "current_wallpaper", None) or ""
        self.item_entry.set_text(str(wid) if wid else "")
        grid.attach(self.item_entry, 1, 1, 2, 1)

        grid.attach(Gtk.Label(label="Steam username:", halign=Gtk.Align.END), 0, 2, 1, 1)
        self.user_entry = Gtk.Entry()
        self.user_entry.set_placeholder_text(
            "For SteamCMD +login — password typed in terminal only"
        )
        self.user_entry.set_text((parent.settings.get("steam_username") or "").strip())
        grid.attach(self.user_entry, 1, 2, 2, 1)

        self.remember_user = Gtk.CheckButton(label="Remember Steam username in settings")
        self.remember_user.set_active(bool((parent.settings.get("steam_username") or "").strip()))
        grid.attach(self.remember_user, 1, 3, 2, 1)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.verify_btn = Gtk.Button(label="Verify local files")
        self.verify_btn.set_tooltip_text(
            "Check project.json and main asset file on disk (no network)"
        )
        self.verify_btn.connect("clicked", self._on_verify_clicked)
        self.bootstrap_btn = Gtk.Button(label="Install SteamCMD")
        self.bootstrap_btn.set_tooltip_text(f"Download Valve SteamCMD into {_STEAMCMD_INSTALL_DIR}")
        self.bootstrap_btn.connect("clicked", self._on_bootstrap_clicked)
        self.terminal_btn = Gtk.Button(label="Repair (SteamCMD terminal)")
        self.terminal_btn.set_tooltip_text(
            "Re-download Workshop content via Valve SteamCMD in a real terminal (+login username only). "
            "Use after verification fails or when files are missing. Password / Steam Guard stay in that terminal."
        )
        self.terminal_btn.connect("clicked", self._on_terminal_clicked)
        self.show_steam_log_btn = Gtk.Button(label="Show last SteamCMD log")
        self.show_steam_log_btn.set_tooltip_text(
            "Load exit code and transcript tail from the last terminal repair "
            "(under ~/.config/linux-wallpaperengine-gtk/)"
        )
        self.show_steam_log_btn.connect("clicked", self._on_show_last_steamcmd_log_clicked)
        btn_row.pack_start(self.verify_btn, False, False, 0)
        btn_row.pack_start(self.bootstrap_btn, False, False, 0)
        btn_row.pack_start(self.terminal_btn, False, False, 0)
        btn_row.pack_start(self.show_steam_log_btn, False, False, 0)
        grid.attach(btn_row, 0, 4, 3, 1)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(160)
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_monospace(True)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scroll.add(self.log_view)
        grid.attach(scroll, 0, 5, 3, 1)

        self.get_content_area().pack_start(grid, True, True, 0)
        self.show_all()

    def _append_log_line(self, text):
        buf = self.log_view.get_buffer()
        buf.insert(buf.get_end_iter(), text + "\n")
        adj = self.log_view.get_parent().get_vadjustment()
        adj.set_value(adj.get_upper())

    def _on_verify_clicked(self, _btn):
        item = self.item_entry.get_text().strip()
        if not item:
            self._append_log_line("Enter a Workshop item ID.")
            return
        root = self.main_window.engine.wallpaper_dir
        ok, msg = workshop_item_local_status(root, item)
        self._append_log_line(msg)
        if ok:
            md = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Local verification OK",
            )
            md.format_secondary_text(msg)
            md.run()
            md.destroy()
            return

        md = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Verification failed — missing or incomplete Workshop files",
        )
        md.format_secondary_text(
            msg + "\n\nYou can open SteamCMD in a terminal to let Steam re-fetch this item "
            "(requires Wallpaper Engine on your account). Password entry stays in that terminal."
        )
        md.add_button("_Ignore", Gtk.ResponseType.CANCEL)
        md.add_button("Repair via SteamCMD…", Gtk.ResponseType.APPLY)
        md.set_default_response(Gtk.ResponseType.APPLY)
        resp = md.run()
        md.destroy()
        if resp == Gtk.ResponseType.APPLY:
            self._run_steamcmd_repair_terminal()

    def _on_bootstrap_clicked(self, _btn):
        self.bootstrap_btn.set_sensitive(False)
        self._append_log_line("Installing SteamCMD (Valve CDN) …")

        def work():
            path = ensure_steamcmd_installed()
            GLib.idle_add(self._bootstrap_done, path)

        threading.Thread(target=work, daemon=True).start()

    def _bootstrap_done(self, path):
        self.bootstrap_btn.set_sensitive(True)
        if path:
            self._append_log_line(f"SteamCMD ready: {path}")
        else:
            self._append_log_line("SteamCMD install failed (network or tar error).")

    def _on_terminal_clicked(self, _btn):
        self._run_steamcmd_repair_terminal()

    def _run_steamcmd_repair_terminal(self):
        """Open SteamCMD in an external terminal to re-download Workshop content (Valve)."""
        item = self.item_entry.get_text().strip()
        user = self.user_entry.get_text().strip()
        if not item or not user:
            self._append_log_line("Workshop item ID and Steam username are required.")
            return
        exe = find_steamcmd()
        if not exe:
            self._append_log_line("SteamCMD not found. Use “Install SteamCMD” first.")
            return
        if launch_steamcmd_workshop_in_terminal(exe, user, item):
            _, transcript, exit_f = steamcmd_sidecar_paths()
            self._append_log_line(
                "Opened a terminal running SteamCMD. If it exits too fast, check errors below — "
                "the shell now waits for Enter before closing. Enter password / Steam Guard only in that terminal."
            )
            self._append_log_line(f"Exit code will be saved to: {exit_f}")
            self._append_log_line(f"Transcript (if script is installed): {transcript}")
            self._append_log_line(
                "Then click “Show last SteamCMD log” or “Verify local files” again."
            )
            if self.remember_user.get_active():
                self.main_window.settings["steam_username"] = user
                self.main_window.save_settings()
        else:
            self._append_log_line(
                "Could not launch a terminal (tried gnome-terminal, konsole, x-terminal-emulator)."
            )

    def _on_show_last_steamcmd_log_clicked(self, _btn):
        _, transcript, exit_f = steamcmd_sidecar_paths()
        self._append_log_line("--- last SteamCMD sidecar ---")
        if os.path.isfile(exit_f):
            try:
                with open(exit_f, encoding="utf-8", errors="replace") as fp:
                    code = fp.read().strip()
                self._append_log_line(f"Exit code file ({exit_f}): {code}")
            except OSError as exc:
                self._append_log_line(f"Could not read exit file: {exc}")
        else:
            self._append_log_line(
                f"No exit code file yet ({exit_f}). Run a repair in terminal first."
            )
        if os.path.isfile(transcript):
            try:
                with open(transcript, encoding="utf-8", errors="replace") as fp:
                    lines = fp.readlines()
                tail = lines[-160:] if len(lines) > 160 else lines
                self._append_log_line(f"--- transcript tail ({transcript}) ---")
                for ln in tail:
                    self._append_log_line(ln.rstrip("\n"))
            except OSError as exc:
                self._append_log_line(f"Could not read transcript: {exc}")
        else:
            self._append_log_line(
                f"No typescript yet ({transcript}). Install util-linux script(1) for transcripts, "
                "or read errors directly in the terminal before pressing Enter."
            )


class EnvironmentDetector:
    """Comprehensive environment detection - works everywhere, assumes nothing"""

    def __init__(self, logger=None):
        self.log = logger or logging.getLogger("EnvironmentDetector")

    def detect_all(self):
        """Detect everything about the environment"""
        return {
            "distro": self._detect_distro(),
            "compositor": self._detect_compositor(),
            "display_server": self._detect_display_server(),
            "desktop": self._detect_desktop_environment(),
            "gpu": self._detect_gpu(),
            "steam_paths": self._detect_steam_paths(),
            "wpe_paths": self._detect_wpe_paths(),
            "capabilities": self._detect_capabilities(),
        }

    def _detect_desktop_environment(self):
        """Detect desktop environment/session (best-effort)."""
        # Common environment variables
        xdg_current = (os.environ.get("XDG_CURRENT_DESKTOP") or "").lower()
        desktop_session = (os.environ.get("DESKTOP_SESSION") or "").lower()
        gdm_session = (os.environ.get("GDMSESSION") or "").lower()

        combined = " ".join([xdg_current, desktop_session, gdm_session])

        if "gnome" in combined or "ubuntu" in combined:
            return "gnome"
        if "kde" in combined or "plasma" in combined:
            return "kde"
        if "xfce" in combined:
            return "xfce"
        if "cinnamon" in combined:
            return "cinnamon"
        if "mate" in combined:
            return "mate"

        return "unknown"

    def _detect_distro(self):
        """Detect Linux distribution using multiple methods"""
        # Method 1: /etc/os-release (systemd standard)
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro_id = line.split("=")[1].strip().strip('"').lower()
                        # Handle ID_LIKE for better detection
                        if distro_id in ["ubuntu", "debian", "linuxmint", "pop"]:
                            return distro_id
                        # Check ID_LIKE line
                        f.seek(0)
                        for line in f:
                            if line.startswith("ID_LIKE="):
                                id_like = line.split("=")[1].strip().strip('"').lower()
                                if "debian" in id_like:
                                    return "debian"
                                elif "fedora" in id_like:
                                    return "fedora"
                                elif "arch" in id_like:
                                    return "arch"
                        return distro_id
        except Exception as e:
            self.log.debug(f"os-release detection failed: {e}")

        # Method 2: /etc/lsb-release (Debian/Ubuntu)
        try:
            with open("/etc/lsb-release") as f:
                for line in f:
                    if line.startswith("DISTRIB_ID="):
                        return line.split("=")[1].strip().strip('"').lower()
        except Exception:
            pass

        # Method 3: Check for distro-specific files
        distro_indicators = {
            "/etc/arch-release": "arch",
            "/etc/fedora-release": "fedora",
            "/etc/redhat-release": "rhel",
            "/etc/SuSE-release": "suse",
            "/etc/debian_version": "debian",
            "/etc/gentoo-release": "gentoo",
            "/etc/nixos/configuration.nix": "nixos",
        }

        for path, distro in distro_indicators.items():
            if os.path.exists(path):
                return distro

        return "unknown"

    def _detect_compositor(self):
        """Detect windowing compositor"""
        # Check for Wayland
        if os.environ.get("WAYLAND_DISPLAY"):
            # Try to detect specific Wayland compositor
            try:
                result = subprocess.run(
                    ["pgrep", "-f", "mutter|kwin|sway|river|hyprland"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if result.returncode == 0:
                    stdout = result.stdout.lower()
                    if "mutter" in stdout:
                        return "mutter"  # GNOME
                    elif "kwin" in stdout:
                        return "kwin"  # KDE
                    elif "sway" in stdout:
                        return "sway"
                    elif "hyprland" in stdout:
                        return "hyprland"
                    elif "river" in stdout:
                        return "river"
            except Exception:
                pass
            return "wayland-unknown"

        # Check for X11
        if os.environ.get("DISPLAY"):
            # Try to detect X11 window manager
            try:
                result = subprocess.run(
                    ["xprop", "-root", "_NET_WM_NAME"], capture_output=True, text=True, timeout=1
                )
                if result.returncode == 0:
                    # Parse window manager name
                    wm_name = result.stdout.strip()
                    if "openbox" in wm_name.lower():
                        return "openbox"
                    elif "xfce" in wm_name.lower():
                        return "xfce"
            except Exception:
                pass
            return "x11"

        return "unknown"

    def _detect_display_server(self):
        """Detect display server with full context"""
        wayland = os.environ.get("WAYLAND_DISPLAY")
        x11 = os.environ.get("DISPLAY")

        if wayland and x11:
            return "xwayland"  # Running X11 apps on Wayland
        elif wayland:
            return "wayland"
        elif x11:
            return "x11"
        else:
            return "none"

    def _detect_gpu(self):
        """Detect GPU and driver"""
        gpu_info = {
            "vendor": "unknown",
            "driver": "unknown",
            "model": "unknown",
        }

        # Method 1: lspci (most reliable)
        try:
            result = subprocess.run(["lspci", "-nnk"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "VGA" in line or "3D" in line or "Display" in line:
                        if "AMD" in line or "ATI" in line or "Radeon" in line:
                            gpu_info["vendor"] = "amd"
                            # Try to extract model
                            if "RX" in line:
                                gpu_info["model"] = "radeon-rx"
                            elif "R9" in line:
                                gpu_info["model"] = "radeon-r9"
                        elif "NVIDIA" in line:
                            gpu_info["vendor"] = "nvidia"
                        elif "Intel" in line:
                            gpu_info["vendor"] = "intel"
        except Exception as e:
            self.log.debug(f"lspci detection failed: {e}")

        # Method 2: Check driver modules
        try:
            result = subprocess.run(["lsmod"], capture_output=True, text=True, timeout=1)
            if result.returncode == 0:
                stdout = result.stdout.lower()
                if "amdgpu" in stdout:
                    gpu_info["driver"] = "amdgpu"
                elif "radeon" in stdout:
                    gpu_info["driver"] = "radeonsi"
                elif "nvidia" in stdout:
                    gpu_info["driver"] = "nvidia"
                elif "i915" in stdout:
                    gpu_info["driver"] = "intel"
        except Exception:
            pass

        return gpu_info

    def _detect_steam_paths(self):
        """Detect Steam paths using XDG + distro conventions"""
        paths = []
        home = os.path.expanduser("~")

        # XDG Base Directory Standard
        xdg_data_home = os.environ.get("XDG_DATA_HOME", os.path.join(home, ".local", "share"))
        paths.append(
            os.path.join(xdg_data_home, "Steam", "steamapps", "workshop", "content", "431960")
        )

        # Standard locations
        standard_paths = [
            os.path.join(home, ".steam", "steam", "steamapps", "workshop", "content", "431960"),
            os.path.join(home, ".steam", "root", "steamapps", "workshop", "content", "431960"),
            os.path.join(
                home, ".local", "share", "Steam", "steamapps", "workshop", "content", "431960"
            ),
        ]
        paths.extend(standard_paths)

        # Distro-specific paths
        distro = self._detect_distro()
        if distro == "nixos":
            paths.append(
                os.path.join(
                    home,
                    ".nix-profile",
                    "share",
                    "steam",
                    "steamapps",
                    "workshop",
                    "content",
                    "431960",
                )
            )
        elif distro == "arch":
            paths.append("/usr/share/steam/steamapps/workshop/content/431960")

        # Flatpak paths
        paths.append(
            os.path.join(
                home,
                ".var",
                "app",
                "com.valvesoftware.Steam",
                ".local",
                "share",
                "Steam",
                "steamapps",
                "workshop",
                "content",
                "431960",
            )
        )

        # Snaps paths
        paths.append(
            os.path.join(
                home,
                "snap",
                "steam",
                "common",
                ".local",
                "share",
                "Steam",
                "steamapps",
                "workshop",
                "content",
                "431960",
            )
        )

        # Return only existing paths
        return [p for p in paths if os.path.isdir(p)]

    def _detect_wpe_paths(self):
        """Detect linux-wallpaperengine binary using all methods"""
        paths = []

        # Method 1: PATH environment variable
        try:
            result = subprocess.run(
                ["which", "linux-wallpaperengine"], capture_output=True, text=True, timeout=1
            )
            if result.returncode == 0:
                paths.append(result.stdout.strip())
        except Exception:
            pass

        # Method 2: Standard system paths
        system_paths = [
            "/usr/local/bin/linux-wallpaperengine",
            "/usr/bin/linux-wallpaperengine",
            "/opt/linux-wallpaperengine/linux-wallpaperengine",
            "/usr/local/games/linux-wallpaperengine",
        ]
        paths.extend(system_paths)

        # Method 3: XDG-based user paths
        home = os.path.expanduser("~")
        xdg_bin_home = os.environ.get("XDG_BIN_HOME", os.path.join(home, ".local", "bin"))
        paths.append(os.path.join(xdg_bin_home, "linux-wallpaperengine"))

        # Method 4: Common build locations (relative to script)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        relative_paths = [
            # This repository's bundled upstream submodule build output
            os.path.join(
                script_dir,
                "upstream",
                "linux-wallpaperengine",
                "build",
                "output",
                "linux-wallpaperengine",
            ),
            os.path.join(
                script_dir,
                "..",
                "upstream",
                "linux-wallpaperengine",
                "build",
                "output",
                "linux-wallpaperengine",
            ),
            os.path.join(
                script_dir,
                "..",
                "linux-wallpaperengine",
                "build",
                "output",
                "linux-wallpaperengine",
            ),
            os.path.join(
                script_dir, "..", "linux-wallpaperengine", "build", "linux-wallpaperengine"
            ),
            os.path.join(script_dir, "linux-wallpaperengine"),
        ]
        paths.extend([os.path.abspath(p) for p in relative_paths])

        # Method 5: Distro-specific package locations
        distro = self._detect_distro()
        if distro == "nixos":
            try:
                result = subprocess.run(
                    [
                        "nix-store",
                        "-q",
                        "--outputs",
                        "/run/current-system/sw/bin/linux-wallpaperengine",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if result.returncode == 0:
                    paths.append(result.stdout.strip())
            except Exception:
                pass

        # Method 6: Check all PATH directories
        path_dirs = os.environ.get("PATH", "").split(":")
        for path_dir in path_dirs:
            if path_dir:  # Skip empty paths
                candidate = os.path.join(path_dir, "linux-wallpaperengine")
                if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                    paths.append(candidate)

        # Return only existing, executable files
        return [p for p in paths if os.path.isfile(p) and os.access(p, os.X_OK)]

    def _detect_capabilities(self):
        """Detect system capabilities"""
        return {
            "docker": self._detect_docker_capabilities(),
            "gtk": self._detect_gtk_capabilities(),
        }

    def _detect_docker_capabilities(self):
        """Detect Docker availability and capabilities"""
        capabilities = {
            "available": False,
            "version": None,
            "user_in_group": False,
            "can_run": False,
            "container_runtime": None,
        }

        # Check for Docker
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                capabilities["available"] = True
                capabilities["version"] = result.stdout.strip()
                capabilities["container_runtime"] = "docker"
        except Exception:
            pass

        # Check for Podman (Docker alternative)
        if not capabilities["available"]:
            try:
                result = subprocess.run(
                    ["podman", "--version"], capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0:
                    capabilities["available"] = True
                    capabilities["version"] = result.stdout.strip()
                    capabilities["container_runtime"] = "podman"
            except Exception:
                pass

        # Check if user can run containers
        if capabilities["available"]:
            try:
                result = subprocess.run(
                    [capabilities["container_runtime"], "ps"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                capabilities["can_run"] = result.returncode == 0
            except Exception:
                pass

        # Check group membership
        try:
            import grp

            username = os.getlogin()
            groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
            if "docker" in groups:
                capabilities["user_in_group"] = True
        except Exception:
            pass

        return capabilities

    def _detect_gtk_capabilities(self):
        """Detect GTK availability and version"""
        capabilities = {
            "available": False,
            "version": None,
            "theme": None,
            "icons": None,
        }

        try:
            import gi

            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk

            capabilities["available"] = True
            capabilities["version"] = (
                f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
            )

            settings = Gtk.Settings.get_default()
            if settings:
                capabilities["theme"] = settings.get_property("gtk-theme-name")
                capabilities["icons"] = settings.get_property("gtk-icon-theme-name")
        except Exception as e:
            self.log.debug(f"GTK detection failed: {e}")

        return capabilities


class WallpaperEngine:
    """Core wallpaper engine functionality"""

    def __init__(self):
        self.log = logging.getLogger("WallpaperEngine")

        # Detect environment upfront (deterministic approach)
        self.env_detector = EnvironmentDetector(self.log)
        self.env = self.env_detector.detect_all()

        # Log detected environment
        self.log.info(
            f"Detected environment: distro={self.env['distro']}, compositor={self.env['compositor']}, display={self.env['display_server']}, gpu={self.env['gpu']['vendor']}/{self.env['gpu']['driver']}"
        )

        # Adaptive initialization based on detection
        self._initialize_adaptive()

        self.current_wallpaper = None
        self.current_process = None  # Track current wallpaper process

    def _initialize_adaptive(self):
        """Initialize based on detected environment"""
        # Display detection (compositor-aware)
        compositor = self.env["compositor"]
        display_server = self.env["display_server"]

        if display_server == "wayland" and compositor in ["sway", "hyprland"]:
            self.display = self._detect_display_wayland(compositor)
        elif display_server in ["x11", "xwayland"]:
            self.display = self._detect_display_x11()
        else:
            self.display = None
            if display_server == "wayland":
                self.log.warning(
                    "Wayland detected - Linux Wallpaper Engine works best on X11/XWayland"
                )
                self.log.warning(
                    "Consider switching to X11 session or using XWayland compatibility"
                )

        # Path resolution (all methods, XDG-based)
        self.wpe_path = self._resolve_wpe_path()
        self.wallpaper_dir = self._resolve_wallpaper_dir()

        # Containerization is DEV/DEBUG only: opt-in via GUI settings.
        # We still detect capabilities so the UI can inform users, but never
        # enable container execution implicitly during normal use.
        self.use_container = False

        # GPU-specific workarounds (default based on detection)
        self.default_workarounds = self._get_gpu_workarounds(self.env["gpu"])

    def _get_x11_screen_geometry(self):
        """Best-effort screen geometry for X11 window mode."""
        try:
            # Prefer xrandr if available (matches our display naming)
            result = subprocess.run(["xrandr"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and self.display:
                for line in result.stdout.splitlines():
                    if line.startswith(self.display) and " connected" in line:
                        # Example: DisplayPort-0 connected primary 2560x1440+0+0 ...
                        parts = line.split()
                        for p in parts:
                            if "x" in p and "+" in p and p.count("+") >= 2:
                                res = p.split("+", 1)[0]
                                w, h = res.split("x", 1)
                                return int(w), int(h)
        except Exception:
            pass

        # Fallback: ask GDK (works for X11 apps)
        try:
            from gi.repository import Gdk

            screen = Gdk.Screen.get_default()
            if screen:
                return int(screen.get_width()), int(screen.get_height())
        except Exception:
            pass

        return 1920, 1080

    def _wallpaper_engine_candidate_pids(self, root_pid, max_depth=6):
        """Root PID plus descendants (mpv, CEF, etc. often own the mapped X11 window)."""
        from collections import deque

        seen = set()
        ordered = []
        queue = deque([(root_pid, 0)])
        while queue:
            pid, depth = queue.popleft()
            if pid <= 0 or pid in seen or depth > max_depth or len(ordered) >= 48:
                continue
            seen.add(pid)
            ordered.append(pid)
            try:
                proc = subprocess.run(
                    ["pgrep", "-P", str(pid)],
                    capture_output=True,
                    text=True,
                    timeout=0.5,
                )
                if proc.returncode != 0 or not proc.stdout.strip():
                    continue
                for line in proc.stdout.strip().splitlines():
                    try:
                        queue.append((int(line.strip()), depth + 1))
                    except ValueError:
                        pass
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                pass
        return ordered

    def _x11_net_wm_pid(self, window_id):
        """Read _NET_WM_PID for an X11 window, or None."""
        try:
            proc = subprocess.run(
                ["xprop", "-id", window_id, "_NET_WM_PID"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if proc.returncode != 0 or "=" not in proc.stdout:
                return None
            tail = proc.stdout.split("=", 1)[1].strip()
            return int(tail.split()[0])
        except (ValueError, subprocess.TimeoutExpired, IndexError):
            return None

    def _xdotool_search_pids(self, pid, only_visible):
        """Return first matching window id for pid, or None."""
        args = ["xdotool", "search"]
        if only_visible:
            args.append("--onlyvisible")
        args.extend(["--pid", str(pid)])
        try:
            proc = subprocess.run(args, capture_output=True, text=True, timeout=1)
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip().splitlines()[0]
        except (subprocess.TimeoutExpired, OSError):
            pass
        return None

    def _find_wallpaper_x11_window(self, root_pid, candidate_pids):
        """Resolve X11 window id: try each PID (visible + not), then WM_CLASS + _NET_WM_PID."""
        for pid in candidate_pids:
            wid = self._xdotool_search_pids(pid, only_visible=False)
            if wid:
                return wid
            wid = self._xdotool_search_pids(pid, only_visible=True)
            if wid:
                return wid

        cand_set = set(candidate_pids)
        for class_flag in ("--class", "--classname"):
            try:
                proc = subprocess.run(
                    ["xdotool", "search", class_flag, "linux-wallpaperengine"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if proc.returncode != 0 or not proc.stdout.strip():
                    continue
                for wid in proc.stdout.strip().splitlines():
                    wid = wid.strip()
                    if not wid:
                        continue
                    net_pid = self._x11_net_wm_pid(wid)
                    if net_pid is not None and net_pid in cand_set:
                        return wid
            except (subprocess.TimeoutExpired, OSError):
                pass
        return None

    def _apply_x11_desktop_hints_to_window(self, wid):
        try:
            subprocess.run(
                ["wmctrl", "-ir", wid, "-b", "add,below,sticky,skip_taskbar,skip_pager"],
                timeout=2,
                capture_output=True,
            )
        except OSError:
            pass
        try:
            subprocess.run(
                [
                    "xprop",
                    "-id",
                    wid,
                    "-f",
                    "_NET_WM_WINDOW_TYPE",
                    "32a",
                    "-set",
                    "_NET_WM_WINDOW_TYPE",
                    "_NET_WM_WINDOW_TYPE_DESKTOP",
                ],
                timeout=2,
                capture_output=True,
            )
        except OSError:
            pass
        try:
            subprocess.run(
                ["wmctrl", "-ir", wid, "-b", "add,fullscreen"],
                timeout=2,
                capture_output=True,
            )
        except OSError:
            pass

    def _apply_gnome_window_hints(self, process):
        """Make window-mode wallpaper behave like a desktop background (GNOME/X11).

        Runs in a background thread with extended search: child PIDs, non-visible windows,
        and WM_CLASS linux-wallpaperengine (see upstream GLFW hints), so we do not block GTK.
        """
        for tool in ("xdotool", "wmctrl", "xprop"):
            if subprocess.run(["which", tool], capture_output=True, text=True).returncode != 0:
                self.log.debug(f"GNOME hints skipped: missing {tool}")
                return

        root_pid = process.pid

        def worker():
            deadline = time.time() + 15.0
            poll = 0.2
            wid = None
            while time.time() < deadline:
                if process.poll() is not None:
                    return
                if getattr(self, "current_process", None) is not process:
                    return
                candidates = self._wallpaper_engine_candidate_pids(root_pid)
                wid = self._find_wallpaper_x11_window(root_pid, candidates)
                if wid:
                    break
                time.sleep(poll)
                poll = min(poll + 0.05, 0.5)

            if not wid:
                self.log.warning(
                    "GNOME desktop hints: no X11 window matched (engine children / class fallback)"
                )
                return
            self._apply_x11_desktop_hints_to_window(wid)
            self.log.info(f"GNOME desktop hints applied (X11 window id {wid})")

        threading.Thread(target=worker, daemon=True, name="gnome-x11-hints").start()

    def _detect_display_x11(self):
        """Detect primary display using xrandr (X11)

        Uses POSIX-compliant subprocess calls without shell injection risks.
        Reference: https://docs.python.org/3/library/subprocess.html#security-considerations
        """
        try:
            # Try primary display first
            # Use subprocess without invoking the shell (security)
            result = subprocess.run(["xrandr"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                # Parse output for primary display
                for line in result.stdout.splitlines():
                    if "primary" in line and "connected" in line:
                        display = line.split()[0]
                        self.log.info(f"Found primary display (X11): {display}")
                        return display

            # Fall back to first connected display
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "connected" in line and "disconnected" not in line:
                        display = line.split()[0]
                        self.log.info(f"Using display (X11): {display}")
                        return display

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.log.error(f"X11 display detection failed: {e}")
        except Exception as e:
            self.log.error(f"X11 display detection failed: {e}")
        return None

    def _detect_display_wayland(self, compositor):
        """Detect display using Wayland compositor-specific methods"""
        try:
            if compositor == "sway":
                result = subprocess.run(
                    ["swaymsg", "-t", "get_outputs"], capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0:
                    import json

                    outputs = json.loads(result.stdout)
                    for output in outputs:
                        if output.get("active", False):
                            name = output.get("name", "")
                            self.log.info(f"Found active display (Sway): {name}")
                            return name
            elif compositor == "hyprland":
                result = subprocess.run(
                    ["hyprctl", "monitors", "-j"], capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0:
                    import json

                    monitors = json.loads(result.stdout)
                    if monitors:
                        name = monitors[0].get("name", "")
                        self.log.info(f"Found display (Hyprland): {name}")
                        return name
            # Fallback: try XWayland if available
            if os.environ.get("DISPLAY"):
                return self._detect_display_x11()
        except Exception as e:
            self.log.debug(f"Wayland display detection failed: {e}")
            # Fallback to X11 if XWayland available
            if os.environ.get("DISPLAY"):
                return self._detect_display_x11()
        return None

    def _resolve_wpe_path(self):
        """Resolve linux-wallpaperengine binary using deterministic detection"""
        wpe_paths = self.env["wpe_paths"]

        if wpe_paths:
            # Use first found path
            path = wpe_paths[0]
            self.log.info(f"Resolved WPE path: {path}")
            return path
        else:
            self.log.warning("Could not find linux-wallpaperengine binary")
            self.log.warning(
                "Tried: PATH, system paths, XDG paths, relative paths, distro-specific paths"
            )
            return None

    def _resolve_wallpaper_dir(self):
        """Resolve Steam Workshop wallpaper directory using deterministic detection"""
        steam_paths = self.env["steam_paths"]

        if steam_paths:
            # Use first found path
            path = steam_paths[0]
            self.log.info(f"Resolved wallpaper directory: {path}")
            return path
        else:
            self.log.warning("Could not find Steam Workshop wallpaper directory")
            self.log.warning("Tried: XDG paths, standard locations, distro-specific, Flatpak, Snap")
            return None

    def _get_gpu_workarounds(self, gpu_info):
        """Get workarounds based on detected GPU"""
        workarounds = {}

        if gpu_info["driver"] == "radeonsi":
            # AMD RadeonSI - apply all workarounds
            workarounds = {
                "MESA_GL_SYNC_TO_VBLANK": "1",
                "MESA_GL_VERSION_OVERRIDE": "4.5",
                "MESA_GLSL_VERSION_OVERRIDE": "450",
                "MESA_GLSL_CACHE_DISABLE": "1",
                "R600_DEBUG": "nosb,notgsi",
            }
            self.log.info("Detected AMD RadeonSI - workarounds will be applied by default")
        elif gpu_info["driver"] == "intel":
            # Intel - minimal workarounds
            workarounds = {
                "MESA_GL_VERSION_OVERRIDE": "4.5",
            }
            self.log.info("Detected Intel GPU - minimal workarounds available")
        elif gpu_info["driver"] == "nvidia":
            # NVIDIA - usually works fine
            self.log.info("Detected NVIDIA GPU - no workarounds needed")
        else:
            self.log.info(f"GPU driver unknown ({gpu_info['driver']}) - no default workarounds")

        return workarounds

    def _build_docker_command(self, cmd_base, env, wpe_dir):
        """Build standalone docker run command (no external scripts)"""
        container_runtime = self.env["capabilities"]["docker"]["container_runtime"]
        if not container_runtime:
            container_runtime = "docker"  # Fallback

        # Build docker run command
        docker_cmd = [container_runtime, "run", "--rm"]

        # GPU access (required for rendering)
        docker_cmd.extend(["--device=/dev/dri"])

        # X11/Wayland display access
        if env.get("DISPLAY"):
            docker_cmd.extend(["-e", f"DISPLAY={env['DISPLAY']}"])
            docker_cmd.extend(["-v", "/tmp/.X11-unix:/tmp/.X11-unix:rw"])

        # Environment variables
        for key, value in env.items():
            docker_cmd.extend(["-e", f"{key}={value}"])

        # Mount WPE binary and libraries
        wpe_lib_dir = os.path.dirname(self.wpe_path)
        docker_cmd.extend(["-v", f"{wpe_lib_dir}:{wpe_lib_dir}:ro"])
        docker_cmd.extend(["-v", f"{self.wpe_path}:{self.wpe_path}:ro"])

        # Mount wallpaper directory if available
        if self.wallpaper_dir:
            docker_cmd.extend(["-v", f"{self.wallpaper_dir}:{self.wallpaper_dir}:ro"])

        # Working directory
        docker_cmd.extend(["-w", wpe_dir])

        # Security: drop privileges but allow GPU
        docker_cmd.extend(["--security-opt", "seccomp=unconfined"])  # Required for GPU
        docker_cmd.extend(["--cap-add", "SYS_ADMIN"])  # Required for GPU access

        # Resource limits (prevent resource exhaustion)
        docker_cmd.extend(["--memory=4g", "--memory-swap=4g"])
        docker_cmd.extend(["--cpus=4"])

        # Use host network (required for X11/Wayland)
        docker_cmd.append("--network=host")

        # Image (use a base image with required libraries)
        # For standalone operation, try to use existing image or create minimal one
        docker_cmd.append("ubuntu:22.04")  # Base image - user should have this or similar

        # Command to run
        docker_cmd.extend(cmd_base)

        self.log.info(f"Built docker command: {' '.join(docker_cmd[:10])}...")  # Log first part
        return docker_cmd

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

    @staticmethod
    def _read_process_stderr_to_string(process) -> str:
        try:
            if process.stderr:
                return process.stderr.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return ""

    def _log_immediate_wallpaper_failure(self, process) -> None:
        stderr_output = self._read_process_stderr_to_string(process)
        if stderr_output:
            self.log.error(f"Process failed to start. Error output:\n{stderr_output}")
        else:
            self.log.error("Process failed to start (no error output available)")

    def _wallpaper_child_is_running(self, process) -> bool:
        """Whether the child is still running — ``poll()`` + kernel PID facts (no wall-clock wait)."""
        return wallpaper_subprocess_running(
            process,
            on_kill_permission_denied=lambda: self.log.warning(
                "Cannot verify wallpaper child PID (permission); assuming running"
            ),
        )

    def run_wallpaper(self, wallpaper_id, **options):
        """Run wallpaper with specified options"""
        if not all([self.wpe_path, self.display, wallpaper_id]):
            self.log.error(
                f"Missing components - path: {self.wpe_path}, display: {self.display}, id: {wallpaper_id}"
            )
            return False, None

        try:
            # Stop any running wallpaper first
            self.log.info("Stopping current wallpaper...")
            self.stop_wallpaper()

            # Check if containerization should be used
            use_container = options.get("use_container", self.use_container)

            # Save current directory
            original_dir = os.getcwd()
            self.log.debug(f"Original directory: {original_dir}")

            # Change to WPE directory (only if not using container)
            wpe_dir = os.path.dirname(self.wpe_path)
            if not use_container:
                self.log.info(f"Changing to WPE directory: {wpe_dir}")
                os.chdir(wpe_dir)

            # Setup environment variables (needed for both container and non-container modes)
            env = os.environ.copy()

            # Build command - use containerized execution if enabled
            if use_container:
                # Standalone container execution (no external scripts needed)
                self.log.info("Using containerized backend for crash isolation")
                # Build docker run command directly
                docker_cmd = self._build_docker_command(
                    cmd_base=[self.wpe_path], env=env, wpe_dir=wpe_dir
                )
                cmd = docker_cmd
            else:
                cmd = [self.wpe_path]

            # Check if custom arguments contain single-process mode
            using_single_process = (
                options.get("enable_custom_args")
                and options.get("custom_args")
                and "--single-process" in options.get("custom_args", "")
            )

            self.log.debug(
                f"Single-process detection: enable_custom_args={options.get('enable_custom_args')}, custom_args='{options.get('custom_args')}', using_single_process={using_single_process}"
            )

            # Add common options (skip problematic ones if using single-process mode)
            if not using_single_process:
                # Full argument set for normal mode
                if options.get("fps"):
                    cmd.extend(["--fps", str(options["fps"])])
                if options.get("mute"):
                    cmd.append("--silent")
                if "volume" in options:
                    cmd.extend(["--volume", str(int(options["volume"]))])
                if options.get("no_automute"):
                    cmd.append("--noautomute")
                if options.get("no_audio_processing"):
                    cmd.append("--no-audio-processing")
                if options.get("no_fullscreen_pause"):
                    cmd.append("--no-fullscreen-pause")
                if options.get("disable_mouse"):
                    cmd.append("--disable-mouse")
                if options.get("scaling"):
                    cmd.extend(["--scaling", options["scaling"]])
                if options.get("clamp"):
                    cmd.extend(["--clamp", options["clamp"]])
            else:
                # Limited argument set for single-process mode (exclude scaling/clamp)
                self.log.info(
                    "Single-process mode detected - excluding problematic scaling/clamp arguments"
                )
                if options.get("fps"):
                    cmd.extend(["--fps", str(options["fps"])])
                if options.get("mute"):
                    cmd.append("--silent")
                if "volume" in options:
                    cmd.extend(["--volume", str(int(options["volume"]))])
                if options.get("no_automute"):
                    cmd.append("--noautomute")
                if options.get("no_audio_processing"):
                    cmd.append("--no-audio-processing")
                if options.get("no_fullscreen_pause"):
                    cmd.append("--no-fullscreen-pause")
                if options.get("disable_mouse"):
                    cmd.append("--disable-mouse")
                # Skip scaling and clamp - they break argument parsing in single-process mode

            # Add custom arguments if enabled
            if options.get("enable_custom_args") and options.get("custom_args"):
                custom_args = options["custom_args"].strip()
                if custom_args:
                    # Split custom arguments properly (handle quoted strings)
                    import shlex

                    try:
                        custom_args_list = shlex.split(custom_args)
                        cmd.extend(custom_args_list)
                        self.log.info(f"Added custom arguments: {custom_args_list}")
                    except ValueError as e:
                        self.log.error(f"Invalid custom arguments syntax: {e}")

            # GNOME/X11 compatibility: GNOME often draws the desktop background itself,
            # so the engine's screen-root mode can be invisible. In that case, run in
            # window mode fullscreen and apply desktop-like window hints.
            gnome_compat = bool(options.get("gnome_compat", False))
            if (
                gnome_compat
                and self.env.get("desktop") == "gnome"
                and self.env.get("display_server") in ["x11", "xwayland"]
                and not use_container
            ):
                w, h = self._get_x11_screen_geometry()
                cmd.extend(["--window", f"0x0x{w}x{h}", wallpaper_id])
            else:
                # Default: screen-root mode
                cmd.extend(["--screen-root", self.display, wallpaper_id])

            self.log.info(f"Running command: {' '.join(map(str, cmd))}")

            # CRITICAL WORKAROUND: Apply radeonsi driver crash workarounds
            # These prevent SIGSEGV in radeonsi_dri.so without disabling GPU
            # Workarounds are controlled by options (default: enabled)
            if options.get("enable_radeonsi_workarounds", True):
                workarounds_applied = []

                # Sync to VBlank (prevents race conditions)
                if options.get("radeonsi_sync_to_vblank", True):
                    env["MESA_GL_SYNC_TO_VBLANK"] = "1"
                    workarounds_applied.append("sync_to_vblank")

                # OpenGL version override (stable API)
                if options.get("radeonsi_gl_version_override", True):
                    env["MESA_GL_VERSION_OVERRIDE"] = "4.5"
                    env["MESA_GLSL_VERSION_OVERRIDE"] = "450"
                    workarounds_applied.append("gl_version_override")

                # Disable shader cache (prevents corruption)
                if options.get("radeonsi_disable_shader_cache", True):
                    env["MESA_GLSL_CACHE_DISABLE"] = "1"
                    env["MESA_GLSL_CACHE_MAX_SIZE"] = "0"
                    workarounds_applied.append("disable_shader_cache")

                # Enable error checking (catches issues early)
                if options.get("radeonsi_enable_error_checking", True):
                    env["MESA_NO_ERROR"] = "0"
                    workarounds_applied.append("error_checking")

                # Disable aggressive optimizations
                if options.get("radeonsi_disable_aggressive_opts", True):
                    env["R600_DEBUG"] = "nosb,notgsi"
                    workarounds_applied.append("disable_aggressive_opts")

                # Always set these for stability
                env["MESA_LOADER_DRIVER_OVERRIDE"] = "radeonsi"
                env["LIBGL_ALWAYS_INDIRECT"] = "0"
                env["GALLIUM_HUD"] = "simple,fps"

                if workarounds_applied:
                    self.log.info(
                        f"Applied radeonsi driver workarounds: {', '.join(workarounds_applied)}"
                    )
                else:
                    self.log.info(
                        "radeonsi workarounds enabled but all individual options disabled"
                    )
            else:
                self.log.info("radeonsi driver workarounds disabled by user")

            # For containerized mode, environment is passed via docker -e flags
            # Workarounds are included in env dict and passed to container
            if not use_container:
                # Add LD_PRELOAD if enabled (non-containerized)
                if options.get("enable_ld_preload"):
                    libcef_path = os.path.join(wpe_dir, "libcef.so")
                    if os.path.exists(libcef_path):
                        env["LD_PRELOAD"] = libcef_path
                        self.log.info(f"Added LD_PRELOAD: {libcef_path}")
                    else:
                        self.log.warning(
                            f"libcef.so not found at {libcef_path}, skipping LD_PRELOAD"
                        )

                # Add mouse Y-axis inversion workaround if enabled
                if options.get("invert_mouse_y"):
                    env["MOUSE_Y_INVERT"] = "1"
                    self.log.info("Mouse Y-axis inversion enabled (workaround for coordinate bug)")

            # Create new process with stable configuration
            # Capture stderr to log errors if process fails
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,  # Capture stderr to diagnose failures
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
                cwd=wpe_dir if not use_container else original_dir,
                env=env,
            )

            if self._wallpaper_child_is_running(process):
                self.current_wallpaper = wallpaper_id
                self.current_process = process
                self.log.info(f"Wallpaper process started successfully (PID: {process.pid})")
                if (
                    gnome_compat
                    and self.env.get("desktop") == "gnome"
                    and self.env.get("display_server") in ["x11", "xwayland"]
                    and not use_container
                ):
                    self._apply_gnome_window_hints(process)
                return True, cmd

            self._log_immediate_wallpaper_failure(process)
            return False, None

        except Exception as e:
            self.log.error(f"Failed to run wallpaper: {str(e)}", exc_info=True)
            return False, None

        finally:
            self.log.debug(f"Returning to original directory: {original_dir}")
            os.chdir(original_dir)

    def stop_wallpaper(self, timeout=10):
        """Stop currently running wallpaper using POSIX-compliant process management.

        Uses proper signal handling (SIGTERM then SIGKILL) and direct process
        object methods when available, falling back to process discovery for
        orphaned or containerized processes.

        Args:
            timeout: Maximum time to spend stopping (seconds). Default 10s.

        Returns:
            bool: True if stopped successfully, False otherwise

        References:
            - Python signal module: https://docs.python.org/3/library/signal.html
            - Python subprocess: https://docs.python.org/3/library/subprocess.html
            - POSIX signals: https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/signal.h.html
            - os.kill: https://docs.python.org/3/library/os.html#os.kill
        """
        start_time = time.time()
        sigterm_timeout = max(2.0, timeout * 0.6)  # 60% of timeout for graceful termination
        sigkill_timeout = max(1.0, timeout * 0.3)  # 30% for force kill

        try:
            self.log.info("Stopping wallpaper processes...")

            # Step 1: Stop tracked process object directly (most efficient)
            if self.current_process is not None:
                try:
                    pid = self.current_process.pid
                    self.log.debug(f"Terminating tracked process (PID: {pid})")

                    # Send SIGTERM for graceful shutdown
                    # Reference: https://docs.python.org/3/library/subprocess.Popen.html#subprocess.Popen.terminate
                    self.current_process.terminate()

                    # Wait for graceful termination with timeout
                    # Reference: https://docs.python.org/3/library/subprocess.Popen.html#subprocess.Popen.wait
                    try:
                        self.current_process.wait(timeout=sigterm_timeout)
                        self.log.debug(f"Process {pid} terminated gracefully")
                    except subprocess.TimeoutExpired:
                        self.log.warning(f"Process {pid} did not terminate, sending SIGKILL")
                        # Force kill if graceful termination failed
                        # Reference: https://docs.python.org/3/library/subprocess.Popen.html#subprocess.Popen.kill
                        self.current_process.kill()
                        try:
                            self.current_process.wait(timeout=sigkill_timeout)
                            self.log.debug(f"Process {pid} killed")
                        except subprocess.TimeoutExpired:
                            self.log.error(f"Process {pid} failed to die even after SIGKILL")
                            return False

                except (ProcessLookupError, ValueError) as e:
                    # Process already dead or invalid PID
                    self.log.debug(f"Tracked process already terminated: {e}")
                except Exception as e:
                    self.log.warning(f"Error stopping tracked process: {e}")

            # Step 2: Stop Docker containers (if any)
            # Reference: Docker CLI docs - https://docs.docker.com/engine/reference/commandline/ps/
            self._stop_docker_containers()

            # Step 3: Clean up any orphaned processes by pattern matching
            # This handles cases where process was started outside this instance
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time > 0.5:  # Only if we have time left
                if not self._stop_orphaned_processes(remaining_time):
                    self.log.warning("Some orphaned processes may still be running")

            # Clean up state
            self.current_process = None
            self.current_wallpaper = None

            elapsed = time.time() - start_time
            self.log.info(f"Wallpaper stopped successfully in {elapsed:.2f}s")
            return True

        except Exception as e:
            self.log.error(f"Failed to stop wallpaper: {e}", exc_info=True)
            return False

    def _stop_docker_containers(self):
        """Stop Docker containers running wallpaper engine.

        Uses Docker CLI without shell injection vulnerabilities.
        Reference: https://docs.docker.com/engine/reference/commandline/ps/
        """
        try:
            # List containers without shell expansion
            # Reference: https://docs.python.org/3/library/subprocess.html#security-considerations
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=lwpe-backend", "--format", "{{.ID}}"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                container_ids = [
                    cid.strip() for cid in result.stdout.strip().split("\n") if cid.strip()
                ]
                for cid in container_ids:
                    self.log.info(f"Stopping Docker container: {cid}")
                    # Stop container
                    subprocess.run(["docker", "stop", cid], timeout=5, check=False)
                    # Remove container
                    subprocess.run(["docker", "rm", cid], timeout=5, check=False)

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Docker not available or timed out - not an error
            pass
        except Exception as e:
            self.log.debug(f"Error stopping Docker containers: {e}")

    def _stop_orphaned_processes(self, timeout):
        """Stop orphaned processes matching wallpaper engine pattern.

        Uses POSIX signals directly via os.kill() instead of shell commands.
        Reference: https://docs.python.org/3/library/os.html#os.kill

        Args:
            timeout: Maximum time to spend on cleanup

        Returns:
            bool: True if all processes stopped, False otherwise
        """
        try:
            # Find processes by executable path
            # Reference: pgrep(1) - POSIX-compliant process search
            # Use word boundary to avoid matching this GTK app
            pattern = f"{self.wpe_path}\\b"
            result = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )

            if result.returncode != 0:
                # No processes found
                return True

            # Parse PIDs
            pids = []
            for line in result.stdout.strip().split("\n"):
                pid_str = line.strip()
                if pid_str:
                    try:
                        pids.append(int(pid_str))
                    except ValueError:
                        continue

            if not pids:
                return True

            self.log.debug(f"Found {len(pids)} orphaned process(es): {pids}")

            # Send SIGTERM to all processes
            # Reference: https://docs.python.org/3/library/signal.html#signal.SIGTERM
            for pid in pids:
                try:
                    # Reference: https://docs.python.org/3/library/os.html#os.kill
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    # Process already dead
                    continue
                except PermissionError:
                    self.log.warning(f"Permission denied killing process {pid}")
                    continue
                except Exception as e:
                    self.log.debug(f"Error sending SIGTERM to {pid}: {e}")

            # Wait until each PID is gone from the kernel or we hit the deadline (no fixed blind sleep)
            sigterm_deadline = time.monotonic() + min(2.0, timeout * 0.5)
            while any(_pid_exists(p) for p in pids) and time.monotonic() < sigterm_deadline:
                time.sleep(0.005)

            remaining_pids = [pid for pid in pids if _pid_exists(pid)]

            if remaining_pids:
                self.log.debug(f"Force killing {len(remaining_pids)} process(es): {remaining_pids}")
                # Send SIGKILL to remaining processes
                # Reference: https://docs.python.org/3/library/signal.html#signal.SIGKILL
                for pid in remaining_pids:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        continue
                    except Exception as e:
                        self.log.debug(f"Error sending SIGKILL to {pid}: {e}")

                sigkill_deadline = time.monotonic() + min(1.0, timeout * 0.3)
                while (
                    any(_pid_exists(p) for p in remaining_pids)
                    and time.monotonic() < sigkill_deadline
                ):
                    time.sleep(0.005)

            return True

        except subprocess.TimeoutExpired:
            self.log.warning("Process discovery timed out")
            return False
        except Exception as e:
            self.log.debug(f"Error stopping orphaned processes: {e}")
            return False

    def _is_wayland(self):
        """Check if running under Wayland (uses detected environment)"""
        return self.env["display_server"] in ["wayland", "xwayland"]


class WallpaperWindow(Gtk.Window):
    def __init__(self, initial_settings=None):
        super().__init__(title="Linux Wallpaper Engine")
        self.set_default_size(800, 600)

        # Initialize engine
        self.engine = WallpaperEngine()

        # Setup logging
        self.log = logging.getLogger("GUI")

        # Preview size (default 200x120)
        self.preview_width = 200
        self.preview_height = 120

        # Playlist support
        self.playlist_timeout = None
        self.playlist_active = False

        # Default settings
        self.settings = {
            "fps": 60,
            "volume": 100,
            "mute": False,
            "mouse_enabled": True,
            "invert_mouse_y": False,  # Workaround for vertical axis inversion bug
            "auto_rotation": False,
            "rotation_interval": 15,
            "no_automute": False,
            "no_audio_processing": False,
            "no_fullscreen_pause": False,
            "scaling": "default",
            "clamp": "clamp",
            "enable_custom_args": False,
            "custom_args": "",
            "enable_ld_preload": False,
            # Containerization (DEV/DEBUG): opt-in only
            "enable_containerization": False,
            "enable_gnome_compat": True,
            # radeonsi driver crash workarounds
            "enable_radeonsi_workarounds": True,  # Default enabled for safety
            "radeonsi_sync_to_vblank": True,
            "radeonsi_gl_version_override": True,
            "radeonsi_disable_shader_cache": True,
            "radeonsi_enable_error_checking": True,
            "radeonsi_disable_aggressive_opts": True,
            # Steam Workshop helper — optional remembered Steam username (no secrets)
            "steam_username": "",
        }

        # Merge initial settings with defaults
        if initial_settings:
            self.settings.update(initial_settings)

        # Load saved settings (including paths) BEFORE anything else
        self.load_settings()

        # Initialize UI
        self._setup_ui()

        # Load wallpapers
        self.load_wallpapers()

        # Connect delete-event instead of destroy to intercept close
        self.connect("delete-event", self.on_destroy)
        # Also observe actual destroy, so a programmatic destroy still terminates cleanly.
        self.connect("destroy", self._on_window_destroyed)

        # Add CSS provider for styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(
            b"""
            .current-wallpaper {
                border: 3px solid @selected_bg_color;
                border-radius: 4px;
                padding: 2px;
            }
        """
        )
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Setup system tray
        self.setup_tray_icon()

        # Check if setup is needed
        GLib.idle_add(self.check_initial_setup)

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
        self.volume_icon = Gtk.Image.new_from_icon_name(
            "audio-volume-high-symbolic", Gtk.IconSize.SMALL_TOOLBAR
        )
        self.mute_button.add(self.volume_icon)
        self.mute_button.set_tooltip_text("Toggle Mute")
        self.mute_button.connect("toggled", self.on_mute_toggled)
        vol_box.pack_start(self.mute_button, False, False, 0)

        # Volume slider
        self.last_volume = 100  # Store last volume before mute
        adjustment = Gtk.Adjustment(
            value=100, lower=0, upper=100, step_increment=1, page_increment=10, page_size=0
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
            value=100,  # Default value (100%)
            lower=50,  # Minimum 50%
            upper=200,  # Maximum 200%
            step_increment=10,  # Small step
            page_increment=25,  # Large step
            page_size=0,  # Required for scales
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
            ("view-refresh-symbolic", "Refresh Wallpapers", self.on_refresh_clicked),
            ("applications-system-symbolic", "Setup Paths", self.on_setup_clicked),
            ("preferences-system-symbolic", "Settings", self.on_settings_clicked),
            ("folder-remote-symbolic", "Steam Workshop", self.on_steam_workshop_clicked),
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
        self.preview_width = int(200 * percentage)  # Base width * scale
        self.preview_height = int(120 * percentage)  # Base height * scale
        self.reload_wallpapers()

    def load_wallpapers(self):
        """Load and display wallpaper previews"""

        def load_preview(wallpaper_id):
            wallpaper_path = os.path.join(self.engine.wallpaper_dir, wallpaper_id)

            # Skip if directory doesn't exist
            if not os.path.exists(wallpaper_path):
                return

            preview_path = None

            # Look for preview image
            for ext in [".gif", ".png", ".jpg", ".webp", ".jpeg"]:
                path = os.path.join(wallpaper_path, f"preview{ext}")
                if os.path.exists(path):
                    preview_path = path
                    break

            # If no preview.* file found, look for any image file as fallback
            if not preview_path:
                for filename in os.listdir(wallpaper_path):
                    if filename.lower().endswith((".gif", ".png", ".jpg", ".jpeg", ".webp")):
                        preview_path = os.path.join(wallpaper_path, filename)
                        break

            # Skip if no image found at all
            if not preview_path:
                return

            # Load actual image preview
            def add_preview():
                try:
                    box = Gtk.Box()
                    box.set_margin_start(2)
                    box.set_margin_end(2)
                    box.set_margin_top(2)
                    box.set_margin_bottom(2)

                    # Handle GIF animations
                    if preview_path.lower().endswith(".gif"):
                        try:
                            animation = GdkPixbuf.PixbufAnimation.new_from_file(preview_path)
                            if animation.is_static_image():
                                pixbuf = animation.get_static_image().scale_simple(
                                    self.preview_width,
                                    self.preview_height,
                                    GdkPixbuf.InterpType.BILINEAR,
                                )
                                image = Gtk.Image.new_from_pixbuf(pixbuf)
                            else:
                                # Animated GIF
                                iter = animation.get_iter(None)
                                first_frame = iter.get_pixbuf()
                                scale_x = self.preview_width / first_frame.get_width()
                                scale_y = self.preview_height / first_frame.get_height()
                                scale = min(scale_x, scale_y)

                                frames = []
                                iter = animation.get_iter(None)
                                while True:
                                    pixbuf = iter.get_pixbuf()
                                    new_width = int(pixbuf.get_width() * scale)
                                    new_height = int(pixbuf.get_height() * scale)
                                    scaled_frame = pixbuf.scale_simple(
                                        new_width, new_height, GdkPixbuf.InterpType.BILINEAR
                                    )
                                    frames.append(scaled_frame)
                                    if not iter.advance():
                                        break

                                image = Gtk.Image()
                                current_frame = 0

                                def update_frame():
                                    nonlocal current_frame
                                    if len(frames) > 0:
                                        image.set_from_pixbuf(frames[current_frame])
                                        current_frame = (current_frame + 1) % len(frames)
                                    return True

                                GLib.timeout_add(50, update_frame)
                        except Exception:
                            # Fallback to static image
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                                preview_path, self.preview_width, self.preview_height, True
                            )
                            image = Gtk.Image.new_from_pixbuf(pixbuf)
                    else:
                        # Static images
                        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                            preview_path, self.preview_width, self.preview_height, True
                        )
                        image = Gtk.Image.new_from_pixbuf(pixbuf)

                    box.add(image)
                    box.wallpaper_id = wallpaper_id
                    self.flowbox.add(box)
                    box.show_all()

                    if wallpaper_id == self.engine.current_wallpaper:
                        self.highlight_current_wallpaper(box)

                except Exception as e:
                    self.log.error(f"Failed to load preview {preview_path}: {e}")

            GLib.idle_add(add_preview)

        # Clear existing previews
        self.flowbox.foreach(lambda w: w.destroy())

        # Load new previews
        wallpapers = self.engine.get_wallpaper_list()
        self.status_label.set_text(f"Loading {len(wallpapers)} wallpapers...")

        for i, wallpaper_id in enumerate(wallpapers):

            def load_with_delay(wid):
                thread = threading.Thread(target=load_preview, args=(wid,))
                thread.daemon = True
                thread.start()

            GLib.timeout_add(i * 5, lambda wid=wallpaper_id: load_with_delay(wid) or False)

    def reload_wallpapers(self):
        """Reload wallpapers with current preview size"""
        self.load_wallpapers()

    def highlight_current_wallpaper(self, current_box=None):
        """Update the highlight for the current wallpaper"""
        # Remove highlight from all boxes
        for child in self.flowbox.get_children():
            box = child.get_child()
            box.get_style_context().remove_class("current-wallpaper")

        # Add highlight to current box
        if current_box:
            current_box.get_style_context().add_class("current-wallpaper")

    def update_current_wallpaper(self, wallpaper_id):
        """Update UI to reflect current wallpaper"""
        # Update status
        if wallpaper_id:
            self.status_label.set_text(f"Current: {wallpaper_id}")
        else:
            self.status_label.set_text("No wallpaper active")

        # Find and highlight the current wallpaper box
        for child in self.flowbox.get_children():
            box = child.get_child()
            if hasattr(box, "wallpaper_id") and box.wallpaper_id == wallpaper_id:
                self.highlight_current_wallpaper(box)
                # Get the scrolled window and scroll to the child's position
                # Get scroll adjustment - use ScrolledWindow API directly
                scrolled_window = child.get_parent().get_parent()
                if isinstance(scrolled_window, Gtk.ScrolledWindow):
                    adj = scrolled_window.get_vadjustment()
                else:
                    # Fallback: try deprecated method if ScrolledWindow check fails
                    adj = getattr(scrolled_window, "get_vadjustment", lambda: None)()
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
            self.status_label.set_text(
                "Wallpaper not started (cancelled, incomplete Workshop files, or engine error)"
            )

    def _workshop_assets_allow_load(self, wallpaper_id):
        """
        If Workshop folder is incomplete, prompt before starting the engine.
        Returns True to proceed, False to abort (user cancelled or chose to open repair dialog).
        """
        root = self.engine.wallpaper_dir
        if not root or not wallpaper_id:
            return True
        ok, msg = workshop_item_local_status(root, wallpaper_id)
        if ok:
            return True

        md = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Workshop files missing or incomplete",
        )
        md.format_secondary_text(
            msg + "\n\nThis item probably will not render until Steam re-downloads it "
            "(Wallpaper Engine on your account)."
        )
        md.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        md.add_button("_Try anyway", Gtk.ResponseType.NO)
        md.add_button("Repair…", Gtk.ResponseType.APPLY)
        md.set_default_response(Gtk.ResponseType.APPLY)
        resp = md.run()
        md.destroy()

        if resp == Gtk.ResponseType.NO:
            return True
        if resp == Gtk.ResponseType.APPLY:
            dlg = SteamWorkshopDialog(self, preset_item_id=str(wallpaper_id))
            dlg.run()
            dlg.destroy()
            self.status_label.set_text(
                "Use Steam Workshop dialog to verify or repair, then select this wallpaper again."
            )
            return False
        return False

    def _load_wallpaper(self, wallpaper_id, skip_workshop_asset_check=False):
        """Load wallpaper with current settings."""
        if not skip_workshop_asset_check:
            if not self._workshop_assets_allow_load(wallpaper_id):
                return False, None
        return self.engine.run_wallpaper(
            wallpaper_id,
            use_container=bool(self.settings.get("enable_containerization", False)),
            gnome_compat=bool(self.settings.get("enable_gnome_compat", True)),
            fps=self.settings["fps"],
            volume=self.settings["volume"],
            mute=self.settings["mute"],
            no_automute=self.settings["no_automute"],
            no_audio_processing=self.settings["no_audio_processing"],
            disable_mouse=self.settings["mouse_enabled"],
            invert_mouse_y=self.settings.get("invert_mouse_y", False),
            no_fullscreen_pause=self.settings["no_fullscreen_pause"],
            scaling=self.settings["scaling"],
            clamp=self.settings["clamp"],
            enable_custom_args=self.settings["enable_custom_args"],
            custom_args=self.settings["custom_args"],
            enable_ld_preload=self.settings["enable_ld_preload"],
            # radeonsi driver workarounds
            enable_radeonsi_workarounds=self.settings.get("enable_radeonsi_workarounds", True),
            radeonsi_sync_to_vblank=self.settings.get("radeonsi_sync_to_vblank", True),
            radeonsi_gl_version_override=self.settings.get("radeonsi_gl_version_override", True),
            radeonsi_disable_shader_cache=self.settings.get("radeonsi_disable_shader_cache", True),
            radeonsi_enable_error_checking=self.settings.get(
                "radeonsi_enable_error_checking", True
            ),
            radeonsi_disable_aggressive_opts=self.settings.get(
                "radeonsi_disable_aggressive_opts", True
            ),
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

    def on_refresh_clicked(self, button):
        """Refresh wallpaper list"""
        self.status_label.set_text("Refreshing wallpaper list...")
        self.load_wallpapers()
        self.status_label.set_text("Wallpaper list refreshed")

    def on_steam_workshop_clicked(self, button):
        """Steam Workshop verify / SteamCMD download (Valve tooling)."""
        dlg = SteamWorkshopDialog(self)
        dlg.run()
        dlg.destroy()

    def on_setup_clicked(self, button):
        """Open setup dialog for path configuration"""
        dialog = SettingsDialog(self)

        # Switch to the Paths tab automatically
        notebook = dialog.get_content_area().get_children()[0]
        notebook.set_current_page(5)  # Paths tab is the 6th tab (0-indexed)

        response = dialog.run()

        if response != Gtk.ResponseType.OK:
            dialog.destroy()
            return

        try:
            # Handle path changes only
            new_wpe_path = dialog.wpe_entry.get_text().strip()
            new_wallpaper_dir = dialog.wallpaper_entry.get_text().strip()

            paths_changed = False
            if new_wpe_path != (self.engine.wpe_path or ""):
                if new_wpe_path and os.path.isfile(new_wpe_path):
                    self.engine.wpe_path = new_wpe_path
                    paths_changed = True
                    self.log.info(f"Updated wallpaper engine path: {new_wpe_path}")
                elif new_wpe_path:
                    self.status_label.set_text("Error: Invalid wallpaper engine path")
                    dialog.destroy()
                    return

            if new_wallpaper_dir != (self.engine.wallpaper_dir or ""):
                if new_wallpaper_dir and os.path.isdir(new_wallpaper_dir):
                    self.engine.wallpaper_dir = new_wallpaper_dir
                    paths_changed = True
                    self.log.info(f"Updated wallpaper directory: {new_wallpaper_dir}")
                elif new_wallpaper_dir:
                    self.status_label.set_text("Error: Invalid wallpaper directory")
                    dialog.destroy()
                    return

            # Reload wallpapers if paths changed
            if paths_changed:
                self.status_label.set_text("Reloading wallpapers...")
                self.save_settings()  # Save paths immediately
                self.load_wallpapers()
            else:
                self.status_label.set_text("No path changes made")

        except Exception as e:
            self.log.error(f"Failed to apply setup: {e}")
        finally:
            dialog.destroy()

    def on_settings_clicked(self, button):
        """Open settings dialog"""
        dialog = SettingsDialog(self)
        response = dialog.run()

        if response != Gtk.ResponseType.OK:
            dialog.destroy()  # Destroy dialog first to prevent GTK warnings
            return  # Don't apply settings if cancelled

        try:
            # Save settings including paths
            settings = {
                "fps": dialog.fps_spin.get_value_as_int(),
                "volume": self.settings["volume"],  # Keep current volume
                "mute": self.settings["mute"],  # Keep current mute state
                "mouse_enabled": dialog.mouse_switch.get_active(),
                "invert_mouse_y": dialog.invert_mouse_y_switch.get_active(),
                "auto_rotation": dialog.rotation_switch.get_active(),
                "rotation_interval": dialog.interval_spin.get_value_as_int(),
                "no_automute": dialog.no_automute_switch.get_active(),
                "no_audio_processing": dialog.no_audio_processing_switch.get_active(),
                "no_fullscreen_pause": dialog.no_fullscreen_pause_switch.get_active(),
                "scaling": dialog.scaling_combo.get_active_text(),
                "clamp": dialog.clamp_combo.get_active_text(),
                "enable_custom_args": dialog.custom_args_switch.get_active(),
                "custom_args": dialog.custom_args_entry.get_text().strip(),
                "enable_ld_preload": dialog.ld_preload_switch.get_active(),
                "enable_containerization": dialog.containerization_switch.get_active(),
                "enable_gnome_compat": dialog.gnome_compat_switch.get_active(),
                # radeonsi driver workarounds
                "enable_radeonsi_workarounds": dialog.radeonsi_workarounds_switch.get_active(),
                "radeonsi_sync_to_vblank": dialog.radeonsi_sync_switch.get_active(),
                "radeonsi_gl_version_override": dialog.radeonsi_gl_version_switch.get_active(),
                "radeonsi_disable_shader_cache": dialog.radeonsi_shader_cache_switch.get_active(),
                "radeonsi_enable_error_checking": dialog.radeonsi_error_check_switch.get_active(),
                "radeonsi_disable_aggressive_opts": dialog.radeonsi_aggressive_opts_switch.get_active(),
            }

            # Handle path changes
            new_wpe_path = dialog.wpe_entry.get_text().strip()
            new_wallpaper_dir = dialog.wallpaper_entry.get_text().strip()

            paths_changed = False
            if new_wpe_path != (self.engine.wpe_path or ""):
                if new_wpe_path and os.path.isfile(new_wpe_path):
                    self.engine.wpe_path = new_wpe_path
                    paths_changed = True
                    self.log.info(f"Updated wallpaper engine path: {new_wpe_path}")
                elif new_wpe_path:
                    self.status_label.set_text("Error: Invalid wallpaper engine path")
                    dialog.destroy()
                    return

            if new_wallpaper_dir != (self.engine.wallpaper_dir or ""):
                if new_wallpaper_dir and os.path.isdir(new_wallpaper_dir):
                    self.engine.wallpaper_dir = new_wallpaper_dir
                    paths_changed = True
                    self.log.info(f"Updated wallpaper directory: {new_wallpaper_dir}")
                elif new_wallpaper_dir:
                    self.status_label.set_text("Error: Invalid wallpaper directory")
                    dialog.destroy()
                    return

            # Apply settings (includes workarounds)
            self.apply_settings(settings)

            # Reload wallpapers if paths changed
            if paths_changed:
                self.status_label.set_text("Reloading wallpapers...")
                self.save_settings()  # Save paths immediately
                self.load_wallpapers()

        except Exception as e:
            self.log.error(f"Failed to apply settings: {e}")
        finally:
            dialog.destroy()  # Destroy dialog

    def apply_settings(self, settings):
        """Apply settings to current and future wallpapers"""
        # Store settings
        self.settings = settings
        self.save_settings()  # Save settings to file

        # Update current wallpaper if running
        if self.engine.current_wallpaper:
            success, cmd = self._load_wallpaper(
                self.engine.current_wallpaper, skip_workshop_asset_check=True
            )
            if success and cmd:
                self.update_command_status(cmd)

        # Handle auto-rotation
        if settings["auto_rotation"]:
            self.start_playlist_rotation(settings["rotation_interval"])
        else:
            self.stop_playlist_rotation()

    def start_playlist_rotation(self, interval):
        """Start automatic wallpaper rotation"""
        if self.playlist_timeout:
            GLib.source_remove(self.playlist_timeout)

        def rotate_wallpaper():
            if wallpaper_id := self.engine.get_next_wallpaper():
                success, _cmd = self._load_wallpaper(wallpaper_id)
                if success:
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

    def setup_tray_icon(self):
        """Setup system tray icon"""
        # Create tray icon
        use_app_indicator = HAS_APP_INDICATOR
        if use_app_indicator:
            # Use AppIndicator3 for better integration
            try:
                self.tray_icon = AppIndicator3.Indicator.new(
                    "linux-wallpaperengine-gtk",
                    "preferences-desktop-wallpaper",
                    AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
                )
                self.tray_icon.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
                self.tray_menu = self.create_tray_menu()
                self.tray_icon.set_menu(self.tray_menu)
                self.tray_icon_type = "appindicator"
                self.log.info("System tray icon created (AppIndicator3)")
            except Exception as e:
                self.log.warning(f"Failed to create AppIndicator3: {e}, falling back to StatusIcon")
                use_app_indicator = False

        if not use_app_indicator:
            # Fallback to Gtk.StatusIcon
            self.tray_icon = Gtk.StatusIcon()
            self.tray_icon.set_from_icon_name("preferences-desktop-wallpaper")
            self.tray_icon.set_tooltip_text("Linux Wallpaper Engine")
            self.tray_icon.connect("activate", self.on_tray_icon_activate)
            self.tray_icon.connect("popup-menu", self.on_tray_icon_popup)
            self.tray_icon_type = "statusicon"
            self.log.info("System tray icon created (StatusIcon)")

        self.tray_visible = True

    def create_tray_menu(self):
        """Create context menu for tray icon"""
        menu = Gtk.Menu()

        # Show/Hide Window
        show_item = Gtk.MenuItem(label="Show Window")
        show_item.connect("activate", self.on_show_window)
        menu.append(show_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Quick Controls
        prev_item = Gtk.MenuItem(label="Previous Wallpaper")
        prev_item.connect("activate", lambda w: self.on_prev_clicked(None))
        menu.append(prev_item)

        next_item = Gtk.MenuItem(label="Next Wallpaper")
        next_item.connect("activate", lambda w: self.on_next_clicked(None))
        menu.append(next_item)

        random_item = Gtk.MenuItem(label="Random Wallpaper")
        random_item.connect("activate", lambda w: self.on_random_clicked(None))
        menu.append(random_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Stop Wallpaper
        stop_item = Gtk.MenuItem(label="Stop Wallpaper")
        stop_item.connect("activate", self.on_stop_wallpaper)
        menu.append(stop_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Settings
        settings_item = Gtk.MenuItem(label="Settings")
        settings_item.connect("activate", lambda w: self.on_settings_clicked(None))
        menu.append(settings_item)

        steam_item = Gtk.MenuItem(label="Steam Workshop…")
        steam_item.connect("activate", lambda w: self.on_steam_workshop_clicked(None))
        menu.append(steam_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Quit
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.on_quit)
        menu.append(quit_item)

        menu.show_all()
        return menu

    def on_tray_icon_activate(self, icon):
        """Handle tray icon left-click (show/hide window)"""
        if self.get_visible():
            self.hide()
        else:
            self.show()
            self.present()

    def on_tray_icon_popup(self, icon, button, time):
        """Handle tray icon right-click (show context menu)"""
        menu = self.create_tray_menu()
        menu.popup(None, None, None, None, button, time)

    def on_show_window(self, widget):
        """Show the main window"""
        self.show()
        self.present()

    def on_stop_wallpaper(self, widget):
        """Stop current wallpaper from tray menu"""
        self.engine.stop_wallpaper()
        self.status_label.set_text("Wallpaper stopped")
        self.update_current_wallpaper(None)

    def on_quit(self, widget):
        """Quit the application (robust even with nested dialog loops)."""
        # Always schedule on the GTK main loop.
        GLib.idle_add(self._quit_now)

    def on_destroy(self, window, event=None):
        """Handle window close - hide to tray instead of quitting"""
        # Check if this is a real close event or programmatic quit
        if hasattr(self, "_quitting") and self._quitting:
            # Actually quit
            self.log.info("Shutting down...")
            return False  # Allow default destroy behavior
        else:
            # Hide to tray
            self.log.info("Hiding window to tray")
            self.hide()
            # Return True to prevent default destroy behavior
            return True

    def _on_window_destroyed(self, *_args):
        # If something destroyed the window (or we destroyed it ourselves), ensure the
        # main loop(s) are told to exit. This prevents “blank window / stuck tray icon”
        # states when a nested Gtk.Dialog.run() loop is active.
        if hasattr(self, "_quitting") and self._quitting:
            self._quit_main_loops()

    def _quit_main_loops(self):
        try:
            while Gtk.main_level() > 0:
                Gtk.main_quit()
        except Exception:
            # If Gtk.main_level isn't available for some reason, fall back to one quit.
            try:
                Gtk.main_quit()
            except Exception:
                pass

    def _quit_now(self):
        # Idempotent: multiple quit triggers should be safe.
        if getattr(self, "_quitting", False):
            self._quit_main_loops()
            return False

        self.log.info("Quitting application...")
        self._quitting = True

        # Stop wallpaper before quitting (best-effort).
        try:
            self.engine.stop_wallpaper()
        except Exception as e:
            self.log.debug(f"stop_wallpaper during quit failed: {e}")

        # Remove tray icon if it exists so the DE doesn't keep a stale item.
        try:
            if hasattr(self, "tray_icon") and self.tray_icon:
                self.tray_icon.set_visible(False)
        except Exception:
            pass

        # Destroy the window if it's still around.
        try:
            self.destroy()
        except Exception:
            pass

        self._quit_main_loops()
        return False

    def on_mute_toggled(self, button):
        """Handle mute button toggle"""
        is_muted = button.get_active()

        # Update settings
        self.settings["mute"] = is_muted

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
            success, cmd = self._load_wallpaper(
                self.engine.current_wallpaper, skip_workshop_asset_check=True
            )
            if success and cmd:
                self.update_command_status(cmd)

    def on_volume_changed(self, scale):
        """Handle volume scale changes"""
        volume = scale.get_value()

        # Update settings
        self.settings["volume"] = volume
        self.settings["mute"] = volume == 0

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
            success, cmd = self._load_wallpaper(
                self.engine.current_wallpaper, skip_workshop_asset_check=True
            )
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
                with open(config_file, "r") as f:
                    saved_settings = json.load(f)
                    # Update defaults with saved settings
                    self.settings.update(saved_settings)

                    # Load engine paths if saved
                    if "wpe_path" in saved_settings and saved_settings["wpe_path"]:
                        self.engine.wpe_path = saved_settings["wpe_path"]
                        self.log.info(
                            f"Loaded saved wallpaper engine path: {saved_settings['wpe_path']}"
                        )

                    if "wallpaper_dir" in saved_settings and saved_settings["wallpaper_dir"]:
                        self.engine.wallpaper_dir = saved_settings["wallpaper_dir"]
                        self.log.info(
                            f"Loaded saved wallpaper directory: {saved_settings['wallpaper_dir']}"
                        )

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

            # Include engine paths in settings
            settings_to_save = self.settings.copy()
            settings_to_save["wpe_path"] = self.engine.wpe_path
            settings_to_save["wallpaper_dir"] = self.engine.wallpaper_dir

            with open(config_file, "w") as f:
                json.dump(settings_to_save, f, indent=4)
                self.log.debug(f"Saved settings with paths: {settings_to_save}")
        except Exception as e:
            self.log.error(f"Failed to save settings: {e}")

    def check_initial_setup(self):
        """Check if initial setup is needed"""
        # Check for Wayland first
        if self.engine.env["display_server"] in ["wayland", "xwayland"]:
            dialog = Gtk.MessageDialog(
                parent=self,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Wayland Session Detected!",
            )
            dialog.format_secondary_text(
                "⚠️ Linux Wallpaper Engine is NOT compatible with Wayland sessions.\n\n"
                "Wallpapers will not display properly or may not work at all.\n\n"
                "Please log out and select an X11/Xorg session instead.\n"
                "Look for options like 'Ubuntu on Xorg' or 'GNOME on Xorg' on your login screen."
            )
            dialog.run()
            dialog.destroy()

        if not self.engine.wpe_path or not self.engine.wallpaper_dir:
            self.log.info("Initial setup needed - opening settings dialog")

            # Show a helpful message
            dialog = Gtk.MessageDialog(
                parent=self,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Setup Required",
            )
            dialog.format_secondary_text(
                "Linux Wallpaper Engine GTK needs to be configured.\n\n"
                "Please specify:\n"
                "• Path to linux-wallpaperengine executable\n"
                "• Steam Workshop wallpaper directory\n\n"
                "The settings dialog will open to configure these paths."
            )
            dialog.run()
            dialog.destroy()

            # Open settings dialog
            self.on_setup_clicked(None)
        return False  # Don't repeat this idle callback


class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Settings", parent=parent, flags=0)
        self.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK)

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
        self.fps_spin.set_value(self.current_settings["fps"])
        perf_grid.attach(fps_label, 0, 0, 1, 1)
        perf_grid.attach(self.fps_spin, 1, 0, 1, 1)

        # Audio settings
        audio_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(audio_grid, Gtk.Label(label="Audio"))

        # Audio switches
        switches = [
            (
                "Keep Playing When Other Apps Play Sound",
                "no_automute_switch",
                "no_automute",
                "By default, wallpaper audio is muted when other applications play sound. "
                + "Enable this to keep wallpaper audio playing.",
            ),
            (
                "Disable Audio Effects",
                "no_audio_processing_switch",
                "no_audio_processing",
                "Disables all audio post-processing effects that may be defined in the wallpaper. "
                + "Can improve performance or fix audio issues.",
            ),
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
        scaling_mode = self.current_settings.get("scaling", "default")
        self.scaling_combo.set_active(
            ["default", "stretch", "fit", "fill"].index(scaling_mode or "default")
        )
        display_grid.attach(scale_label, 0, 0, 1, 1)
        display_grid.attach(self.scaling_combo, 1, 0, 1, 1)

        # clamp mode
        clamp_label = Gtk.Label(label="clamp Mode:", halign=Gtk.Align.END)
        self.clamp_combo = Gtk.ComboBoxText()
        for mode in ["clamp", "border", "repeat"]:
            self.clamp_combo.append_text(mode)
        clamp_mode = self.current_settings.get("clamp", "clamp")
        self.clamp_combo.set_active(["clamp", "border", "repeat"].index(clamp_mode or "clamp"))
        display_grid.attach(clamp_label, 0, 1, 1, 1)
        display_grid.attach(self.clamp_combo, 1, 1, 1, 1)

        # Add interaction settings after audio settings
        interact_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(interact_grid, Gtk.Label(label="Interaction"))

        # Mouse interaction
        self.mouse_switch = Gtk.Switch()
        self.mouse_switch.set_active(self.current_settings["mouse_enabled"])
        mouse_label = Gtk.Label(label="Disable Mouse Interaction:", halign=Gtk.Align.END)
        interact_grid.attach(mouse_label, 0, 0, 1, 1)
        interact_grid.attach(self.mouse_switch, 1, 0, 1, 1)

        # Mouse Y-axis inversion (workaround for coordinate bug)
        self.invert_mouse_y_switch = Gtk.Switch()
        self.invert_mouse_y_switch.set_active(self.current_settings.get("invert_mouse_y", False))
        invert_y_label = Gtk.Label(label="Invert Mouse Y-Axis:", halign=Gtk.Align.END)
        invert_y_label.set_tooltip_text(
            "Workaround for vertical axis mouse coordinate inversion bug"
        )
        interact_grid.attach(invert_y_label, 0, 1, 1, 1)
        interact_grid.attach(self.invert_mouse_y_switch, 1, 1, 1, 1)

        # Fullscreen pause
        self.no_fullscreen_pause_switch = Gtk.Switch()
        self.no_fullscreen_pause_switch.set_active(self.current_settings["no_fullscreen_pause"])
        pause_label = Gtk.Label(label="Disable Fullscreen Pause:", halign=Gtk.Align.END)
        interact_grid.attach(pause_label, 0, 2, 1, 1)
        interact_grid.attach(self.no_fullscreen_pause_switch, 1, 2, 1, 1)

        # Add playlist settings after interaction settings
        playlist_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(playlist_grid, Gtk.Label(label="Playlist"))

        # Auto-rotation
        self.rotation_switch = Gtk.Switch()
        self.rotation_switch.set_active(self.current_settings["auto_rotation"])
        rotation_label = Gtk.Label(label="Enable Auto-rotation:", halign=Gtk.Align.END)
        playlist_grid.attach(rotation_label, 0, 0, 1, 1)
        playlist_grid.attach(self.rotation_switch, 1, 0, 1, 1)

        # Rotation interval
        interval_label = Gtk.Label(label="Rotation Interval (minutes):", halign=Gtk.Align.END)
        self.interval_spin = Gtk.SpinButton.new_with_range(1, 1440, 1)
        self.interval_spin.set_value(self.current_settings["rotation_interval"])
        playlist_grid.attach(interval_label, 0, 1, 1, 1)
        playlist_grid.attach(self.interval_spin, 1, 1, 1, 1)

        # Add paths configuration tab
        paths_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(paths_grid, Gtk.Label(label="Paths"))

        # Wallpaper Engine Path
        wpe_label = Gtk.Label(label="Wallpaper Engine Path:", halign=Gtk.Align.END)
        wpe_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.wpe_entry = Gtk.Entry()
        self.wpe_entry.set_text(parent.engine.wpe_path or "")
        self.wpe_entry.set_placeholder_text("Path to linux-wallpaperengine executable")
        wpe_browse_btn = Gtk.Button(label="Browse...")
        wpe_browse_btn.connect("clicked", self.on_browse_wpe_path)
        wpe_box.pack_start(self.wpe_entry, True, True, 0)
        wpe_box.pack_start(wpe_browse_btn, False, False, 0)
        paths_grid.attach(wpe_label, 0, 0, 1, 1)
        paths_grid.attach(wpe_box, 1, 0, 1, 1)

        # Wallpaper Directory Path
        wallpaper_label = Gtk.Label(label="Wallpaper Directory:", halign=Gtk.Align.END)
        wallpaper_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.wallpaper_entry = Gtk.Entry()
        self.wallpaper_entry.set_text(parent.engine.wallpaper_dir or "")
        self.wallpaper_entry.set_placeholder_text("Steam Workshop wallpaper directory")
        wallpaper_browse_btn = Gtk.Button(label="Browse...")
        wallpaper_browse_btn.connect("clicked", self.on_browse_wallpaper_dir)
        wallpaper_box.pack_start(self.wallpaper_entry, True, True, 0)
        wallpaper_box.pack_start(wallpaper_browse_btn, False, False, 0)
        paths_grid.attach(wallpaper_label, 0, 1, 1, 1)
        paths_grid.attach(wallpaper_box, 1, 1, 1, 1)

        desktop_shortcut_label = Gtk.Label(label="Menu shortcut:", halign=Gtk.Align.END)
        desktop_shortcut_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.install_desktop_btn = Gtk.Button(label="Install menu shortcut…")
        self.install_desktop_btn.set_tooltip_text(
            "Create ~/.local/share/applications/linux-wallpaperengine-gtk.desktop "
            "so the app appears in GNOME Activities, the dash, and KDE menus."
        )
        self.install_desktop_btn.connect("clicked", self.on_install_desktop_clicked)
        desktop_shortcut_box.pack_start(self.install_desktop_btn, False, False, 0)
        paths_grid.attach(desktop_shortcut_label, 0, 2, 1, 1)
        paths_grid.attach(desktop_shortcut_box, 1, 2, 1, 1)

        # Help text
        help_label = Gtk.Label()
        help_label.set_markup(
            "<i>If paths are not detected automatically, use the Browse buttons to locate:\n• linux-wallpaperengine executable\n• Steam Workshop content directory (usually ~/.steam/steam/steamapps/workshop/content/431960)</i>"
        )
        help_label.set_line_wrap(True)
        help_label.set_max_width_chars(50)
        paths_grid.attach(help_label, 0, 3, 2, 1)

        # Add Advanced CEF Arguments tab (after paths configuration)
        advanced_grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        notebook.append_page(advanced_grid, Gtk.Label(label="Advanced"))

        # Enable custom arguments
        self.custom_args_switch = Gtk.Switch()
        self.custom_args_switch.set_active(self.current_settings.get("enable_custom_args", False))
        custom_args_label = Gtk.Label(label="Enable Custom CEF Arguments:", halign=Gtk.Align.END)
        custom_args_label.set_tooltip_text(
            "Enable custom CEF arguments for compatibility fixes and advanced options"
        )
        advanced_grid.attach(custom_args_label, 0, 0, 1, 1)
        advanced_grid.attach(self.custom_args_switch, 1, 0, 1, 1)

        # Custom arguments entry
        args_label = Gtk.Label(label="Custom Arguments:", halign=Gtk.Align.END)
        self.custom_args_entry = Gtk.Entry()
        self.custom_args_entry.set_text(self.current_settings.get("custom_args", ""))
        self.custom_args_entry.set_placeholder_text("e.g., --no-sandbox --single-process")
        self.custom_args_entry.set_tooltip_text(
            "Additional command-line arguments for linux-wallpaperengine"
        )
        advanced_grid.attach(args_label, 0, 1, 1, 1)
        advanced_grid.attach(self.custom_args_entry, 1, 1, 1, 1)

        # Presets dropdown
        presets_label = Gtk.Label(label="Quick Presets:", halign=Gtk.Align.END)
        self.presets_combo = Gtk.ComboBoxText()
        self.presets_combo.append_text("Custom...")
        self.presets_combo.append_text("Intel Graphics Fix (CEF v119+)")
        self.presets_combo.append_text("Debug Mode")
        self.presets_combo.append_text("Performance Mode")
        self.presets_combo.set_active(0)
        self.presets_combo.connect("changed", self.on_preset_changed)
        advanced_grid.attach(presets_label, 0, 2, 1, 1)
        advanced_grid.attach(self.presets_combo, 1, 2, 1, 1)

        # LD_PRELOAD option
        self.ld_preload_switch = Gtk.Switch()
        self.ld_preload_switch.set_active(self.current_settings.get("enable_ld_preload", False))
        ld_preload_label = Gtk.Label(label="Enable LD_PRELOAD Fix:", halign=Gtk.Align.END)
        ld_preload_label.set_tooltip_text(
            "Preload libcef.so to fix CEF v119+ static TLS allocation issues"
        )
        advanced_grid.attach(ld_preload_label, 0, 3, 1, 1)
        advanced_grid.attach(self.ld_preload_switch, 1, 3, 1, 1)

        # Containerization (DEV/DEBUG only) - opt-in
        self.containerization_switch = Gtk.Switch()
        self.containerization_switch.set_active(
            self.current_settings.get("enable_containerization", False)
        )
        container_label = Gtk.Label(label="Enable Containerization (Debug):", halign=Gtk.Align.END)
        container_label.set_tooltip_text(
            "Run wallpapers inside Docker/Podman for isolation. OFF by default; "
            "may fail if the container image lacks GPU/OpenGL runtime dependencies."
        )
        advanced_grid.attach(container_label, 0, 4, 1, 1)
        advanced_grid.attach(self.containerization_switch, 1, 4, 1, 1)

        # GNOME/X11 compatibility (uses window mode + desktop hints)
        self.gnome_compat_switch = Gtk.Switch()
        self.gnome_compat_switch.set_active(self.current_settings.get("enable_gnome_compat", True))
        gnome_label = Gtk.Label(label="GNOME X11 Compatibility:", halign=Gtk.Align.END)
        gnome_label.set_tooltip_text(
            "On GNOME/Xorg the backend often can't draw behind the desktop. "
            "This runs wallpapers in fullscreen window mode and applies desktop-like hints."
        )
        advanced_grid.attach(gnome_label, 0, 5, 1, 1)
        advanced_grid.attach(self.gnome_compat_switch, 1, 5, 1, 1)

        # Separator for GPU driver workarounds
        separator = Gtk.Separator()
        advanced_grid.attach(separator, 0, 6, 2, 1)

        # GPU Driver Crash Workarounds Section
        workaround_header = Gtk.Label()
        workaround_header.set_markup("<b>GPU Driver Crash Workarounds (radeonsi)</b>")
        workaround_header.set_halign(Gtk.Align.START)
        advanced_grid.attach(workaround_header, 0, 7, 2, 1)

        # Enable workarounds master switch
        self.radeonsi_workarounds_switch = Gtk.Switch()
        self.radeonsi_workarounds_switch.set_active(
            self.current_settings.get("enable_radeonsi_workarounds", True)
        )
        workarounds_label = Gtk.Label(label="Enable radeonsi Workarounds:", halign=Gtk.Align.END)
        workarounds_label.set_tooltip_text(
            "Apply Mesa environment variables to prevent GPU driver crashes (SIGSEGV in radeonsi_dri.so). Recommended: ON"
        )
        advanced_grid.attach(workarounds_label, 0, 8, 1, 1)
        advanced_grid.attach(self.radeonsi_workarounds_switch, 1, 8, 1, 1)

        # Individual workaround options (only enabled when master switch is on)
        self.radeonsi_sync_switch = Gtk.Switch()
        self.radeonsi_sync_switch.set_active(
            self.current_settings.get("radeonsi_sync_to_vblank", True)
        )
        self.radeonsi_sync_switch.set_sensitive(self.radeonsi_workarounds_switch.get_active())
        sync_label = Gtk.Label(label="  Sync to VBlank:", halign=Gtk.Align.END)
        sync_label.set_tooltip_text(
            "Force synchronous OpenGL operations (prevents race conditions)"
        )
        advanced_grid.attach(sync_label, 0, 9, 1, 1)
        advanced_grid.attach(self.radeonsi_sync_switch, 1, 9, 1, 1)

        self.radeonsi_gl_version_switch = Gtk.Switch()
        self.radeonsi_gl_version_switch.set_active(
            self.current_settings.get("radeonsi_gl_version_override", True)
        )
        self.radeonsi_gl_version_switch.set_sensitive(self.radeonsi_workarounds_switch.get_active())
        gl_version_label = Gtk.Label(label="  Use OpenGL 4.5 (stable):", halign=Gtk.Align.END)
        gl_version_label.set_tooltip_text("Override to OpenGL 4.5 API (avoids bugs in 4.6)")
        advanced_grid.attach(gl_version_label, 0, 10, 1, 1)
        advanced_grid.attach(self.radeonsi_gl_version_switch, 1, 10, 1, 1)

        self.radeonsi_shader_cache_switch = Gtk.Switch()
        self.radeonsi_shader_cache_switch.set_active(
            self.current_settings.get("radeonsi_disable_shader_cache", True)
        )
        self.radeonsi_shader_cache_switch.set_sensitive(
            self.radeonsi_workarounds_switch.get_active()
        )
        shader_cache_label = Gtk.Label(label="  Disable Shader Cache:", halign=Gtk.Align.END)
        shader_cache_label.set_tooltip_text("Disable shader cache to prevent corruption issues")
        advanced_grid.attach(shader_cache_label, 0, 11, 1, 1)
        advanced_grid.attach(self.radeonsi_shader_cache_switch, 1, 11, 1, 1)

        self.radeonsi_error_check_switch = Gtk.Switch()
        self.radeonsi_error_check_switch.set_active(
            self.current_settings.get("radeonsi_enable_error_checking", True)
        )
        self.radeonsi_error_check_switch.set_sensitive(
            self.radeonsi_workarounds_switch.get_active()
        )
        error_check_label = Gtk.Label(label="  Enable Error Checking:", halign=Gtk.Align.END)
        error_check_label.set_tooltip_text("Enable OpenGL error checking (catches issues early)")
        advanced_grid.attach(error_check_label, 0, 12, 1, 1)
        advanced_grid.attach(self.radeonsi_error_check_switch, 1, 12, 1, 1)

        self.radeonsi_aggressive_opts_switch = Gtk.Switch()
        self.radeonsi_aggressive_opts_switch.set_active(
            self.current_settings.get("radeonsi_disable_aggressive_opts", True)
        )
        self.radeonsi_aggressive_opts_switch.set_sensitive(
            self.radeonsi_workarounds_switch.get_active()
        )
        aggressive_opts_label = Gtk.Label(label="  Disable Aggressive Opts:", halign=Gtk.Align.END)
        aggressive_opts_label.set_tooltip_text("Disable problematic driver optimizations")
        advanced_grid.attach(aggressive_opts_label, 0, 13, 1, 1)
        advanced_grid.attach(self.radeonsi_aggressive_opts_switch, 1, 13, 1, 1)

        # Connect master switch to enable/disable individual options
        self.radeonsi_workarounds_switch.connect(
            "notify::active", self.on_radeonsi_workarounds_toggled
        )

        # Help text for advanced options
        advanced_help = Gtk.Label()
        advanced_help.set_markup(
            "<b>Advanced Options Help:</b>\n\n"
            + "<b>CEF Options:</b>\n"
            + "• <b>Intel Graphics Fix:</b> Solves CEF v119+ crashes\n"
            + "• <b>LD_PRELOAD Fix:</b> Fixes static TLS allocation issues\n\n"
            + "<b>GPU Driver Workarounds:</b>\n"
            + "• <b>radeonsi Workarounds:</b> Prevents SIGSEGV crashes in AMD GPU driver\n"
            + "• <b>Estimated crash reduction:</b> ~70% with all workarounds enabled\n"
            + "• <b>Based on:</b> Analysis of coredumpctl crash reports\n\n"
            + "<i>⚠️ These options fix known compatibility issues but may affect stability</i>"
        )
        advanced_help.set_line_wrap(True)
        advanced_help.set_max_width_chars(60)
        advanced_help.set_halign(Gtk.Align.START)
        advanced_grid.attach(advanced_help, 0, 14, 2, 1)

        # Connect switch to enable/disable entry
        self.custom_args_switch.connect("notify::active", self.on_custom_args_toggled)

        # Initialize the UI state
        self.on_custom_args_toggled(self.custom_args_switch, None)
        self.on_radeonsi_workarounds_toggled(self.radeonsi_workarounds_switch, None)

        self.show_all()

    def on_browse_wpe_path(self, button):
        """Browse for wallpaper engine executable"""
        dialog = Gtk.FileChooserDialog(
            title="Select linux-wallpaperengine executable",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        # Set initial directory
        if self.wpe_entry.get_text():
            dialog.set_filename(self.wpe_entry.get_text())
        else:
            dialog.set_current_folder(os.path.expanduser("~"))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.wpe_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def on_browse_wallpaper_dir(self, button):
        """Browse for wallpaper directory"""
        dialog = Gtk.FileChooserDialog(
            title="Select wallpaper directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        # Set initial directory
        if self.wallpaper_entry.get_text():
            dialog.set_current_folder(self.wallpaper_entry.get_text())
        else:
            # Try to find Steam directory
            for steam_path in [
                "~/.steam/steam/steamapps/workshop/content/431960",
                "~/.local/share/Steam/steamapps/workshop/content/431960",
            ]:
                expanded = os.path.expanduser(steam_path)
                if os.path.exists(expanded):
                    dialog.set_current_folder(expanded)
                    break
            else:
                dialog.set_current_folder(os.path.expanduser("~"))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.wallpaper_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def on_install_desktop_clicked(self, button):
        """Write a Freedesktop .desktop file for GNOME/KDE application menus."""
        ok, result = install_desktop_entry()
        if ok:
            dialog = Gtk.MessageDialog(
                parent=self,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Menu shortcut installed",
            )
            dialog.format_secondary_text(
                "A launcher was written to:\n{}\n\n"
                "It should appear in Activities and the Applications list shortly "
                "(or after logging out and back in).".format(result)
            )
        else:
            dialog = Gtk.MessageDialog(
                parent=self,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Could not install menu shortcut",
            )
            dialog.format_secondary_text(result)
        dialog.run()
        dialog.destroy()

    def on_preset_changed(self, combo):
        """Handle selection of a preset from the advanced options combo box"""
        selected_preset = self.presets_combo.get_active_text()
        if selected_preset == "Intel Graphics Fix (CEF v119+)":
            self.custom_args_entry.set_text("--no-sandbox --single-process")
            self.ld_preload_switch.set_active(True)
        elif selected_preset == "Debug Mode":
            self.custom_args_entry.set_text("--debug-level=2")
            self.ld_preload_switch.set_active(False)
        elif selected_preset == "Performance Mode":
            self.custom_args_entry.set_text("--disable-gpu-vsync --disable-gpu-compositing")
            self.ld_preload_switch.set_active(False)
        elif selected_preset == "Custom...":
            self.custom_args_entry.set_text("")
            self.ld_preload_switch.set_active(False)

    def on_custom_args_toggled(self, switch, gparam):
        """Handle the custom arguments switch toggle"""
        is_active = switch.get_active()
        if is_active:
            self.custom_args_entry.set_sensitive(True)
            self.presets_combo.set_sensitive(True)
            self.ld_preload_switch.set_sensitive(True)
        else:
            self.custom_args_entry.set_sensitive(False)
            self.presets_combo.set_sensitive(False)
            self.ld_preload_switch.set_sensitive(False)

    def on_radeonsi_workarounds_toggled(self, switch, gparam):
        """Handle the radeonsi workarounds master switch toggle"""
        is_active = switch.get_active()
        # Enable/disable individual workaround switches
        self.radeonsi_sync_switch.set_sensitive(is_active)
        self.radeonsi_gl_version_switch.set_sensitive(is_active)
        self.radeonsi_shader_cache_switch.set_sensitive(is_active)
        self.radeonsi_error_check_switch.set_sensitive(is_active)
        self.radeonsi_aggressive_opts_switch.set_sensitive(is_active)


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

        steam_item = Gtk.MenuItem(label="Steam Workshop…")
        steam_item.connect("activate", self.on_steam_workshop_clicked)
        self.append(steam_item)

        remove_item = Gtk.MenuItem(label="Remove local files…")
        remove_item.connect("activate", self.on_remove_local_clicked)
        self.append(remove_item)

        self.show_all()

    def on_apply_clicked(self, widget):
        success, cmd = self.parent._load_wallpaper(self.wallpaper_id)
        if success:
            self.parent.update_current_wallpaper(self.wallpaper_id)
            if cmd:
                self.parent.update_command_status(cmd)

    def on_playlist_clicked(self, widget):
        # TODO: Implement playlist management
        pass

    def on_steam_workshop_clicked(self, widget):
        dlg = SteamWorkshopDialog(self.parent, preset_item_id=self.wallpaper_id)
        dlg.run()
        dlg.destroy()

    def on_remove_local_clicked(self, _widget):
        root = self.parent.engine.wallpaper_dir
        folder = os.path.join(root or "", str(self.wallpaper_id).strip())
        if not os.path.isdir(folder):
            md = Gtk.MessageDialog(
                transient_for=self.parent,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Workshop folder not found",
            )
            md.format_secondary_text(folder)
            md.run()
            md.destroy()
            return

        md = Gtk.MessageDialog(
            transient_for=self.parent,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Remove local Workshop files?",
        )
        md.format_secondary_text(
            "This deletes the local folder for this wallpaper:\n"
            f"{folder}\n\n"
            "It does not unsubscribe you in Steam. You can re-download later via SteamCMD repair."
        )
        md.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        md.add_button("Remove", Gtk.ResponseType.OK)
        md.add_button("Remove + Repair via SteamCMD…", Gtk.ResponseType.APPLY)
        md.set_default_response(Gtk.ResponseType.CANCEL)
        resp = md.run()
        md.destroy()
        if resp not in (Gtk.ResponseType.OK, Gtk.ResponseType.APPLY):
            return

        # If currently running, stop first.
        if str(self.parent.engine.current_wallpaper or "") == str(self.wallpaper_id):
            self.parent.engine.stop_wallpaper()
            self.parent.update_current_wallpaper(None)

        try:
            shutil.rmtree(folder)
            self.parent.status_label.set_text(f"Removed local files for {self.wallpaper_id}.")
        except Exception as e:
            self.parent.status_label.set_text(f"Failed to remove {self.wallpaper_id}: {e}")
            return

        # Refresh list so it disappears.
        try:
            self.parent.load_wallpapers()
        except Exception:
            pass

        if resp == Gtk.ResponseType.APPLY:
            dlg = SteamWorkshopDialog(self.parent, preset_item_id=self.wallpaper_id)
            dlg.run()
            dlg.destroy()


def setup_dev_environment():
    """Setup development environment with all analysis tools.

    Installs pre-commit, analysis tools (ruff, bandit, pylint, mypy, radon, vulture),
    and configures pre-commit hooks. This function replaces the separate setup-dev.sh script.

    References:
        - pre-commit: https://pre-commit.com/
        - ruff: https://docs.astral.sh/ruff/
        - bandit: https://bandit.readthedocs.io/
    """
    print("🔧 Setting up development environment...")
    print()

    # Check if we're in the right directory
    if not os.path.exists("linux-wallpaperengine-gtk.py"):
        print("❌ Error: Must run from project root directory")
        print("   Current directory:", os.getcwd())
        sys.exit(1)

    try:
        # Install pre-commit
        print("📦 Installing pre-commit...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pre-commit"],
            check=True,
            capture_output=True,
        )

        # Install analysis tools
        print("📦 Installing analysis tools...")
        tools = ["ruff", "bandit", "pylint", "mypy", "radon", "vulture"]
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + tools,
            check=True,
            capture_output=True,
        )

        # Install project dev dependencies (if pyproject.toml exists)
        print("📦 Installing project dev dependencies...")
        if os.path.exists("pyproject.toml"):
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError:
                print(
                    "⚠️  Could not install dev dependencies (may need to install PyGObject separately)"
                )

        # Install pre-commit hooks
        print("🔗 Installing pre-commit hooks...")
        subprocess.run(["pre-commit", "install", "--install-hooks"], check=True)

        # Install commit-msg hook
        print("🔗 Installing commit-msg hook...")
        subprocess.run(["pre-commit", "install", "--hook-type", "commit-msg"], check=True)

        print()
        print("✅ Development environment ready!")
        print()
        print("Next steps:")
        print("  - Run 'pre-commit run --all-files' to test all hooks")
        print("  - Run 'pre-commit run ruff --all-files' to test specific hook")
        print("  - Hooks will run automatically on 'git commit'")
        print()
        print("Tools installed:")
        print("  ✓ pre-commit - Git hook framework")
        print("  ✓ ruff - Fast Python linter")
        print("  ✓ bandit - Security linter")
        print("  ✓ pylint - Comprehensive linter")
        print("  ✓ mypy - Static type checker")
        print("  ✓ radon - Complexity checker")
        print("  ✓ vulture - Dead code detector")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error during setup: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: pre-commit command not found after installation")
        print("   Try running: pip install pre-commit")
        sys.exit(1)


def main():
    # Parse command line arguments first (before GTK imports)
    # References:
    # - argparse formatters: https://docs.python.org/3/library/argparse.html#formatter-class
    # - ArgumentDefaultsHelpFormatter: https://docs.python.org/3/library/argparse.html#argparse.ArgumentDefaultsHelpFormatter
    # - RawDescriptionHelpFormatter: https://docs.python.org/3/library/argparse.html#argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        description="""
Linux Wallpaper Engine GTK - A beautiful, deterministic GTK frontend for linux-wallpaperengine.

This application provides a standalone interface to browse, preview, and manage Wallpaper Engine
wallpapers on Linux. It features comprehensive environment detection, graceful degradation, and
works across all major Linux distributions, compositors, and GPU drivers.
        """.strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Launch with default settings
  %(prog)s --fps 30 --volume 50               # Set FPS to 30 and volume to 50%%
  %(prog)s --mute --disable-mouse             # Mute audio and disable mouse interaction
  %(prog)s --scaling fit --clamp border       # Use fit scaling with border clamping
  %(prog)s --setup-dev                        # Setup development environment
  %(prog)s --install-desktop                  # Add Applications menu / Activities launcher (Freedesktop)

For more information, visit:
  https://github.com/abcdqfr/linux-wallpaperengine-gtk
        """.strip(),
    )

    # Development Options (must be first to allow early exit)
    dev_group = parser.add_argument_group(
        "Development Options", "Development and maintenance tools"
    )
    dev_group.add_argument(
        "--setup-dev",
        action="store_true",
        help="Setup development environment (installs pre-commit, linters, and hooks)",
    )
    dev_group.add_argument(
        "--install-desktop",
        action="store_true",
        help="Install Freedesktop .desktop shortcut for GNOME/KDE menus (~/.local/share/applications) and exit",
    )

    # Performance Options
    perf_group = parser.add_argument_group(
        "Performance Options", "Control rendering performance and resource usage"
    )
    perf_group.add_argument(
        "--fps",
        type=int,
        default=60,
        metavar="FPS",
        help="Target frames per second (default: %(default)s)",
    )
    perf_group.add_argument(
        "--scaling",
        choices=["default", "stretch", "fit", "fill"],
        default="default",
        metavar="MODE",
        help="Wallpaper scaling mode: default, stretch, fit, or fill (default: %(default)s)",
    )
    perf_group.add_argument(
        "--clamp",
        choices=["clamp", "border", "repeat"],
        default="clamp",
        metavar="MODE",
        help="Texture clamping mode: clamp, border, or repeat (default: %(default)s)",
    )

    # Audio Options
    audio_group = parser.add_argument_group(
        "Audio Options", "Control audio playback and processing"
    )
    audio_group.add_argument(
        "--volume",
        type=int,
        default=100,
        metavar="PERCENT",
        help="Audio volume (0-100) (default: %(default)s)",
    )
    audio_group.add_argument("--mute", action="store_true", help="Start with audio muted")
    audio_group.add_argument(
        "--no-automute",
        action="store_true",
        help="Disable automatic muting when other applications play audio",
    )
    audio_group.add_argument(
        "--no-audio-processing", action="store_true", help="Disable audio processing effects"
    )

    # Interaction Options
    interaction_group = parser.add_argument_group(
        "Interaction Options", "Control user interaction with wallpapers"
    )
    interaction_group.add_argument(
        "--disable-mouse", action="store_true", help="Disable mouse interaction with wallpapers"
    )
    interaction_group.add_argument(
        "--no-fullscreen-pause",
        action="store_true",
        help="Don't pause wallpapers when applications are fullscreen",
    )

    args = parser.parse_args()

    # Handle --setup-dev early (before GTK imports and dependency checks)
    if args.setup_dev:
        setup_dev_environment()
        sys.exit(0)

    if args.install_desktop:
        ok, result = install_desktop_entry()
        if ok:
            print("Installed menu shortcut:\n  {}".format(result))
            sys.exit(0)
        print("Failed to install menu shortcut: {}".format(result), file=sys.stderr)
        sys.exit(1)

    # Check dependencies first, before any GTK imports
    success, error_msg = check_dependencies()
    if not success:
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    # Setup logging with more verbose output
    logging.basicConfig(
        level=logging.DEBUG,  # Changed from INFO to DEBUG
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler("wallpaper-engine.log"),  # File output
        ],
    )

    logging.info("Starting Linux Wallpaper Engine GTK...")

    # Create and show window
    win = WallpaperWindow(
        initial_settings={
            "fps": args.fps,
            "volume": args.volume,
            "mute": args.mute,
            "mouse_enabled": args.disable_mouse,
            "auto_rotation": False,
            "rotation_interval": 15,
            "no_automute": args.no_automute,
            "no_audio_processing": args.no_audio_processing,
            "no_fullscreen_pause": args.no_fullscreen_pause,
            "scaling": args.scaling,
            "clamp": args.clamp,
        }
    )
    # Don't connect destroy here - let the window handle it (hide to tray)
    # win.connect("destroy", Gtk.main_quit)
    win.show_all()

    # Start GTK main loop
    logging.info("Entering GTK main loop")
    Gtk.main()


if __name__ == "__main__":
    main()
