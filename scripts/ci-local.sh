#!/usr/bin/env bash
# In-house smoke: mirrors `.forgejo/workflows/ci.yml` fast-fail steps (no Docker matrix).
# Uses a repo-local venv (PEP 668–safe) at `.venv-ci/`.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
VENV="${ROOT}/.venv-ci"

if [[ ! -d "${VENV}" ]]; then
  python3 -m venv "${VENV}"
fi
# shellcheck disable=SC1091
source "${VENV}/bin/activate"

python -m pip install -U pip -q
python -m pip install \
  ruff pytest bandit pylint mypy radon vulture black pre-commit pytest-cov pytest-mock \
  -q

echo "==> Pre-commit (byte-compile, pytest, ruff, black, shell/bare-except checks, …)"
pre-commit run --all-files

echo "==> Optional analyzers (informational; match CI continue-on-error)"
bandit -r linux-wallpaperengine-gtk.py wallpaper_process_probe.py scripts tests -ll -f txt 2>/dev/null || true
pylint linux-wallpaperengine-gtk.py --max-line-length=100 -f text || true
mypy linux-wallpaperengine-gtk.py --ignore-missing-imports || true
radon cc linux-wallpaperengine-gtk.py --min B || true
vulture linux-wallpaperengine-gtk.py --min-confidence 80 || true

echo "==> CI local smoke OK"
