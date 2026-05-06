#!/usr/bin/env bash
set -euo pipefail

# Forgejo-only release helper:
# - derives next version from Conventional Commit prefixes since last v* tag
# - bumps pyproject.toml, commits, tags vX.Y.Z, pushes to Forgejo
# - creates a Forgejo Release and uploads:
#   1) linux-wallpaperengine-gtk.py (standalone script)
#   2) source-minimal.tar.gz (small archive of tracked essentials)
#
# Requires LAN Forgejo token file (per project rule):
#   ~/.config/forgejo/api-token

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

OWNER="${FORGEJO_OWNER:-abcdqfr}"
REPO="${FORGEJO_REPO:-linux-wallpaperengine-gtk}"
BASE_URL="${FORGEJO_BASE_URL:-http://127.0.0.1:3080}"
TOKEN_FILE="${FORGEJO_TOKEN_FILE:-${HOME}/.config/forgejo/api-token}"

DRY_RUN=0
EXPLICIT_VERSION=""

usage() {
  cat <<'EOF'
Usage:
  scripts/release.sh [--dry-run] [--version X.Y.Z]

Env (optional):
  FORGEJO_OWNER, FORGEJO_REPO, FORGEJO_BASE_URL, FORGEJO_TOKEN_FILE

Notes:
  - Pushes ONLY to the Forgejo remote via token URL.
  - Creates a Forgejo Release and uploads assets.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --version) EXPLICIT_VERSION="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "missing required tool: $1" >&2; exit 2; }
}
require git
require curl
require python3
require tar

if [[ ! -r "${TOKEN_FILE}" ]]; then
  echo "Forgejo token missing: ${TOKEN_FILE}" >&2
  exit 2
fi
TOKEN="$(cat "${TOKEN_FILE}")"

if [[ -n "$(git status --porcelain || true)" ]]; then
  echo "working tree not clean; commit/stash first" >&2
  exit 2
fi

latest_tag="$(git tag -l 'v*' --sort=-version:refname | head -n 1 || true)"
range="HEAD"
if [[ -n "${latest_tag}" ]]; then
  range="${latest_tag}..HEAD"
fi

commits="$(git log --format=%s "${range}")"
breaking=0
minor=0
patch=0

if git log --format=%B "${range}" | rg -q '^BREAKING CHANGE:'; then breaking=1; fi
if echo "${commits}" | rg -q '^[a-z]+!:'; then breaking=1; fi
if echo "${commits}" | rg -q '^feat(\(.+\))?:'; then minor=1; fi
if echo "${commits}" | rg -q '^fix(\(.+\))?:'; then patch=1; fi

current_version="$(python3 -c "import tomllib, pathlib; p=pathlib.Path('pyproject.toml'); print(tomllib.loads(p.read_text(encoding='utf-8'))['project']['version'])")"

next_version="${EXPLICIT_VERSION}"
if [[ -z "${next_version}" ]]; then
  IFS=. read -r major minor_v patch_v <<<"${current_version}"
  if [[ "${breaking}" -eq 1 ]]; then
    major=$((major+1)); minor_v=0; patch_v=0
  elif [[ "${minor}" -eq 1 ]]; then
    minor_v=$((minor_v+1)); patch_v=0
  elif [[ "${patch}" -eq 1 ]]; then
    patch_v=$((patch_v+1))
  else
    echo "no feat/fix/breaking commits since ${latest_tag:-start}; refusing to bump" >&2
    exit 2
  fi
  next_version="${major}.${minor_v}.${patch_v}"
fi

tag="v${next_version}"
if git rev-parse "${tag}" >/dev/null 2>&1; then
  echo "tag already exists: ${tag}" >&2
  exit 2
fi

echo "current: ${current_version}"
echo "next:    ${next_version}"
echo "tag:     ${tag}"

body="$(cat <<EOF
## Changes
${range}

EOF
)"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "[dry-run] would bump pyproject.toml, commit, tag, push, and create release"
  exit 0
fi

python3 - <<PY
import pathlib, re
p = pathlib.Path("pyproject.toml")
s = p.read_text(encoding="utf-8")
s2, n = re.subn(r'(?m)^version\\s*=\\s*\"[0-9]+\\.[0-9]+\\.[0-9]+\"\\s*$', 'version = "${next_version}"', s, count=1)
if n != 1:
    raise SystemExit("failed to update version in pyproject.toml")
p.write_text(s2, encoding="utf-8")
PY

git add pyproject.toml
git commit -m "chore(release): ${tag}"
git tag -a "${tag}" -m "${tag}"

push_url="http://oauth2:${TOKEN}@127.0.0.1:3080/${OWNER}/${REPO}.git"
git push "${push_url}" main
git push "${push_url}" "${tag}"

mkdir -p dist
cp -f linux-wallpaperengine-gtk.py "dist/linux-wallpaperengine-gtk.py"

# Minimal archive: keep it small and reproducible; include top-level essentials and scripts/tests.
tar -czf "dist/source-minimal.tar.gz" \
  linux-wallpaperengine-gtk.py wallpaper_process_probe.py pyproject.toml README.md LICENSE \
  .pre-commit-config.yaml .gitignore Makefile \
  .forgejo/workflows .github/workflows \
  scripts tests .cursor/rules \
  2>/dev/null

sha256sum dist/* > dist/SHA256SUMS.txt

# Create Forgejo release
release_json="$(python3 - <<PY
import json
print(json.dumps({
  "tag_name": "${tag}",
  "name": "${tag}",
  "body": ${body!r},
  "draft": False,
  "prerelease": False
}))
PY
)"

release_resp="$(curl -fsS \
  -H "Authorization: token ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${release_json}" \
  "${BASE_URL}/api/v1/repos/${OWNER}/${REPO}/releases")"

release_id="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["id"])' <<<"${release_resp}")"

upload() {
  local file="$1"
  local name="$2"
  curl -fsS \
    -H "Authorization: token ${TOKEN}" \
    -H "Content-Type: application/octet-stream" \
    --data-binary @"${file}" \
    "${BASE_URL}/api/v1/repos/${OWNER}/${REPO}/releases/${release_id}/assets?name=${name}" >/dev/null
}

upload "dist/linux-wallpaperengine-gtk.py" "linux-wallpaperengine-gtk.py"
upload "dist/source-minimal.tar.gz" "source-minimal.tar.gz"
upload "dist/SHA256SUMS.txt" "SHA256SUMS.txt"

echo "release created: ${BASE_URL}/${OWNER}/${REPO}/releases/tag/${tag}"

