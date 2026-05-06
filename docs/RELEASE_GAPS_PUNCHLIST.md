## Release readiness punchlist (Forgejo-only)

This repo now has release plumbing (`scripts/release.sh`) and CI checks, but **not** enough gating
to safely enable automated releases. This file tracks what remains.

### Definitions

- **Assisted manual release**: human runs `./scripts/release.sh` after verifying CI is green.
- **Automated release**: CI tags + creates releases on its own (merge-to-main or manual dispatch).

---

### 0. Already done (baseline)

- [x] **Pre-commit as the core gate**: `byte-compile-entrypoints` + `pytest tests/` + Ruff/Black + hygiene.
- [x] **GTK import smoke in CI** (Forgejo `pre-commit` job) so `setup-python` environment can import Gtk.
- [x] **Release assets**: upload **monolithic `linux-wallpaperengine-gtk.py`** and **small source tarball** + `SHA256SUMS.txt`.
- [x] **Monolith still runnable** if `wallpaper_process_probe.py` is missing (release asset usability).

---

### 1. Gating gaps (must-fix before automated release)

- [x] **Conventional commit enforcement in CI**
  - **Why**: `scripts/release.sh` bumps based on commit subjects; without enforcement it’s easy to mint bad versions.
  - **Acceptance**:
    - CI fails if any commit subject in the pushed range does not match agreed patterns:
      - `feat: ...`, `fix: ...`, `chore: ...`, `ci: ...`, `build: ...`, `test: ...`, `docs: ...`
      - optional scope: `type(scope): ...`
      - breaking: `type!: ...` or footer `BREAKING CHANGE: ...`
    - CI also fails if a breaking change is detected but the major bump isn’t performed (release workflow validation).

- [ ] **Release must be tied to a green CI run**
  - **Why**: “tagging broken HEAD” is worse than no releases.
  - **Acceptance**:
    - A dedicated Forgejo Actions workflow `release.yml` exists.
    - It is **manual trigger only** (`workflow_dispatch`) until we trust it.
    - It refuses to run unless required checks are green for the exact commit being released.

- [ ] **Prevent tagging/releasing from dirty or detached states**
  - **Why**: avoid accidental releases from local-only commits or worktrees.
  - **Acceptance**:
    - Release workflow runs in CI only (not from arbitrary local worktrees).
    - Local script remains “assisted manual” and warns if HEAD is not the Forgejo `main` tip.

---

### 2. Coverage gaps (reduce manual testing load)

- [ ] **Headless integration smoke beyond import**
  - **Why**: current tests cover syntax + process probe; regressions still show up in practical use (tray, quit, dialogs).
  - **Acceptance options** (pick one):
    - Add a `--self-test` CLI mode that runs without a display:
      - validates config paths, enumerates wallpapers, performs one local workshop verification, exits 0/1.
    - OR run under Xvfb in CI (harder due to tray/WM specifics) to:
      - create window, exercise quit path, ensure process exits.

- [ ] **Runtime failure visibility (optional but high value)**
  - **Why**: “engine starts then dies” still requires eyeballing logs.
  - **Acceptance**:
    - When the wallpaper subprocess exits after a successful start, surface a user-visible error (status label + log hint).
    - Add a testable seam for this (e.g. child-watch callback invoked in unit tests).

---

### 3. Release hygiene (nice-to-have, but cheap)

- [ ] **Release notes include commit hash + compare range**
  - **Acceptance**:
    - Release body includes the commit SHA and the range used for bump computation (`vX.Y.Z-1..vX.Y.Z`).

- [ ] **Optional signing**
  - **Acceptance**:
    - If you care: tag signing or checksum signing. (Not required for first releases.)

---

### 4. Suggested sequencing

1. Enforce Conventional Commit subjects in CI.
2. Add `release.yml` workflow that is manual-dispatch and depends on green CI.
3. Add `--self-test` mode (no GUI) and run it in CI.
4. Only then consider auto-release (still recommend manual dispatch).
