#!/usr/bin/env bash
set -euo pipefail

TAG="${1:-}"
if [[ -z "${TAG}" ]]; then
  echo "usage: $0 vX.Y.Z" >&2
  exit 2
fi

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

RELEASE_HOST="${RELEASE_HOST:-forgejo}"  # forgejo|github|both
FORGEJO_BASE_URL="${FORGEJO_BASE_URL:-http://127.0.0.1:3080}"
FORGEJO_OWNER="${FORGEJO_OWNER:-abcdqfr}"
FORGEJO_REPO="${FORGEJO_REPO:-linux-wallpaperengine-gtk}"
FORGEJO_TOKEN_FILE="${FORGEJO_TOKEN_FILE:-${HOME}/.config/forgejo/api-token}"

# GitHub uses `gh` auth; do not read tokens here.
GITHUB_OWNER="${GITHUB_OWNER:-abcdqfr}"
GITHUB_REPO="${GITHUB_REPO:-linux-wallpaperengine-gtk}"

tmp="$(mktemp -d)"
cleanup() { rm -rf "${tmp}"; }
trap cleanup EXIT

echo "[assets] tag=${TAG}"

git rev-parse "${TAG}" >/dev/null 2>&1 || { echo "tag not found: ${TAG}" >&2; exit 2; }

commit_sha="$(git rev-parse "${TAG}")"
echo "[assets] commit=${commit_sha}"

# Create artifacts from the tag content without touching working tree.
git archive --format=tar "${TAG}" | tar -xf - -C "${tmp}"
mkdir -p "${tmp}/dist"

cp -f "${tmp}/linux-wallpaperengine-gtk.py" "${tmp}/dist/linux-wallpaperengine-gtk.py"

tar -czf "${tmp}/dist/source-minimal.tar.gz" \
  -C "${tmp}" \
  linux-wallpaperengine-gtk.py wallpaper_process_probe.py pyproject.toml README.md LICENSE \
  .pre-commit-config.yaml .gitignore Makefile \
  .forgejo/workflows .github/workflows \
  scripts/ci-core.sh scripts/ci-local.sh scripts/release.sh tests \
  2>/dev/null || true

(
  cd "${tmp}"
  sha256sum dist/* > dist/SHA256SUMS.txt
)

release_body="$(cat <<EOF
## Commit
${commit_sha}
EOF
)"

publish_github() {
  echo "[github] ensure release exists"
  if ! gh release view "${TAG}" -R "${GITHUB_OWNER}/${GITHUB_REPO}" >/dev/null 2>&1; then
    gh release create "${TAG}" -R "${GITHUB_OWNER}/${GITHUB_REPO}" \
      --title "${TAG}" --notes "${release_body}"
  fi

  echo "[github] upload assets"
  gh release upload "${TAG}" -R "${GITHUB_OWNER}/${GITHUB_REPO}" \
    "${tmp}/dist/linux-wallpaperengine-gtk.py" \
    "${tmp}/dist/source-minimal.tar.gz" \
    "${tmp}/dist/SHA256SUMS.txt" \
    --clobber
}

publish_forgejo() {
  if [[ ! -r "${FORGEJO_TOKEN_FILE}" ]]; then
    echo "forgejo token missing: ${FORGEJO_TOKEN_FILE}" >&2
    exit 2
  fi
  token="$(cat "${FORGEJO_TOKEN_FILE}")"

  api="${FORGEJO_BASE_URL}/api/v1"
  repo_api="${api}/repos/${FORGEJO_OWNER}/${FORGEJO_REPO}"

  echo "[forgejo] ensure release exists"
  release_json="$(TAG="${TAG}" BODY="${release_body}" python3 - <<'PY'
import json, os
print(json.dumps({
  "tag_name": os.environ["TAG"],
  "name": os.environ["TAG"],
  "body": os.environ["BODY"],
  "draft": False,
  "prerelease": False,
}))
PY
)"

  # If not found, create it. If found, we reuse it.
  set +e
  release_resp="$(curl -fsS -H "Authorization: token ${token}" "${repo_api}/releases/tags/${TAG}" 2>/dev/null)"
  rc=$?
  set -e
  if [[ $rc -ne 0 || -z "${release_resp}" ]]; then
    release_resp="$(curl -fsS -H "Authorization: token ${token}" -H "Content-Type: application/json" \
      -d "${release_json}" "${repo_api}/releases")"
  fi

  release_id="$(
    python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["id"])' <<<"${release_resp}"
  )"

  upload() {
    local file="$1"
    local name="$2"
    curl -fsS \
      -H "Authorization: token ${token}" \
      -H "Content-Type: application/octet-stream" \
      --data-binary @"${file}" \
      "${repo_api}/releases/${release_id}/assets?name=${name}" >/dev/null
  }

  echo "[forgejo] upload assets"
  upload "${tmp}/dist/linux-wallpaperengine-gtk.py" "linux-wallpaperengine-gtk.py"
  upload "${tmp}/dist/source-minimal.tar.gz" "source-minimal.tar.gz"
  upload "${tmp}/dist/SHA256SUMS.txt" "SHA256SUMS.txt"
}

case "${RELEASE_HOST}" in
  forgejo) publish_forgejo ;;
  github) publish_github ;;
  both) publish_forgejo; publish_github ;;
  *) echo "invalid RELEASE_HOST: ${RELEASE_HOST} (forgejo|github|both)" >&2; exit 2 ;;
esac

echo "[assets] done"
