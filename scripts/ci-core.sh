#!/usr/bin/env bash
set -euo pipefail

# Canonical core gates (shared by Forgejo + GitHub CI).
# Keep this portable: no GTK apt deps, no secrets, no release logic.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

python -m pip install --upgrade pip
python -m pip install ruff pytest

python - <<'PY'
import re
from pathlib import Path

allowed = {
    "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz",
}

text = Path("linux-wallpaperengine-gtk.py").read_text(encoding="utf-8")
m = re.search(r'^_STEAMCMD_URL\s*=\s*"([^"]+)"\s*$', text, re.M)
if not m:
    raise SystemExit("missing _STEAMCMD_URL assignment")
url = m.group(1)
if url not in allowed:
    raise SystemExit(f"_STEAMCMD_URL not in allowlist: {url}")
print("steamcmd-url-ok", url)
PY

python -m py_compile linux-wallpaperengine-gtk.py wallpaper_process_probe.py
pytest tests/ -v
ruff check linux-wallpaperengine-gtk.py wallpaper_process_probe.py tests/
