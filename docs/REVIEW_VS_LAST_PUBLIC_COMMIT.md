# Review: changes vs last public commit (`origin/main`)

**Purpose:** Single internal reference for what shipped publicly versus what is pending locally, what was simplified versus left unfinished, and remaining gaps.

**Baseline “last public commit”** at time of this review: **`2d0ce5c`** on `origin/main` (published). Anything committed **after** that in your clone exists **only in-house** until you push.

---

## A. Already public — commit `2d0ce5c` vs parent `1a2a250`

**Commit message (abbreviated):** Freedesktop launcher plus CI reliability fixes.

### What changed (files)

| Path                           | Nature of change                                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `linux-wallpaperengine-gtk.py` | **`install_desktop_entry()`**: writes `~/.local/share/applications/linux-wallpaperengine-gtk.desktop` with absolute `Exec=` (`sys.executable` + script path), runs `update-desktop-database` when present; **`--install-desktop`** CLI; **Settings → Paths → “Install menu shortcut…”** button + dialogs.                                                                                                     |
| `.github/workflows/ci.yml`     | Removed **`npm ci`** block from the **pre-commit** job — there is **no** `package.json` in this repository tree, so that step **always failed**. Removed the **`self.settings` grep** “AttributeError” step — that shell pipeline required `WallpaperWindow`/`SettingsDialog` **on the same line** as every `self.settings` use, so it matched almost every legitimate line and was not a valid static check. |
| `.pre-commit-config.yaml`      | Removed the same broken **`check-attribute-errors`** local hook (same flawed heuristic).                                                                                                                                                                                                                                                                                                                      |

### What was _not_ fixed in that commit (scope limits — intentional or not)

| Topic                               | Notes                                                                                                                                                                                                                  |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`pyproject.toml` / Hatch layout** | Still declares `[project.scripts]` pointing at `wallpaperengine.main` and packages under `src/wallpaperengine`, but the tracked tree is **monolith-only**. Packaging/install via `pip install .` was **not** repaired. |
| **Bandit B108** (`/tmp/.X11-unix`)  | Still reported for Docker/X11 bind mounts; CI already treats Bandit as non-blocking. No `# nosec` or refactor.                                                                                                         |
| **Tests**                           | No `tests/` directory in tree; CI does not run pytest.                                                                                                                                                                 |
| **`.jscpdrc.json` / `npx jscpd`**   | Pre-commit references config that may not exist in-repo; **not** audited end-to-end in CI here.                                                                                                                        |
| **Upstream engine binary**          | No submodule or README bridge in **`2d0ce5c`** — “missing backend” after clone-only remained a documentation/repo-structure gap until the follow-up work below.                                                        |

### Assessment

- **CI fixes:** The removed checks were **broken as written**; removing them restores a meaningful signal from Ruff and the `shell=True` grep (after the comment fix below).

- **Desktop integration:** Addresses GNOME/KDE launcher discovery with correct Freedesktop paths; does **not** substitute for installing/building **`linux-wallpaperengine`**.

- **Comment-only fix:** One comment was reworded so **`grep "shell=True"`** did not match **inside a comment** (`# ... shell=True ...`). That grep is brittle; a maintainer could re-break CI by typing those characters in prose again.

---

## B. In-house only (this session — **not pushed** per operator instruction)

### Intended improvements

| Change                                                                                                                               | Rationale                                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Git submodule** `upstream/linux-wallpaperengine` → [Almamu/linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine) | Closes the gap between “clone our repo” and “have upstream source to build.” Uses the **canonical** upstream URL (the old `linux-wallpaperengine/engine` link was invalid / misleading).                                                                                                                                  |
| **`.gitignore`**                                                                                                                     | Allow **`upstream/`**, **`docs/`**, so submodule and internal docs are trackable under the repo’s negated-ignore pattern.                                                                                                                                                                                                 |
| **`README.md`**                                                                                                                      | Documents **`git clone --recurse-submodules`**, **`git submodule update --init --recursive`**, upstream **nested submodules**, **CMake build** path to `build/output/`, PATH / Settings wiring, correct upstream links, curl-only caveat for missing binary, roadmap/contributing wording aligned with submodule reality. |
| **This file**                                                                                                                        | Audit trail vs **`2d0ce5c`** and honest scope notes.                                                                                                                                                                                                                                                                      |

### Submodule caveat

After adding the submodule, **nested** repos under `upstream/linux-wallpaperengine` show as **uninitialized** (`-` in `git submodule status`) until **`git submodule update --init --recursive`** is run **inside** the clone (or equivalent). **Building upstream without that step will fail.** The README states this explicitly.

---

## C. Suggested follow-ups (not done here)

1. Align **`pyproject.toml`** with the monolith or restore a real `src/wallpaperengine` package—pick one strategy.
2. Replace brittle **`grep shell=True`** CI check with a small AST parse or allowlist comments.
3. Add **`tests/`** + minimal pytest smoke (`--install-desktop` dry-run mock, desktop file writer unit test).
4. Either add **`.jscpdrc.json`** to the tree or drop/simplify the jscpd hook so pre-commit is deterministic offline.

---

## D. How to compare trees locally

```bash
# Public baseline vs last pushed commit (already on origin)
git log -1 --oneline origin/main

# After you commit in-house work (not pushed):
git diff origin/main..HEAD --stat
```

**Do not push** until policy allows; keep this document with the branch if you want reviewers to see the same narrative.

---

## E. End-to-end verification (submodule path — executed)

**Environment:** Debian-family host, `linux-wallpaperengine-gtk` checkout with `upstream/linux-wallpaperengine` submodule.

| Step                                                           | Result                                                                                                                                                                                |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `git submodule update --init --recursive`                      | Required nested checkouts; **`src/External/json`** initially failed with empty tree / “Unable to find current revision” until **deinit + `rm -rf` + re-init** (documented in README). |
| Install distro `-dev` packages                                 | CMake failed until **GLEW/GLFW/GLUT** (and related) packages present; follow Almamu README / Ubuntu package list.                                                                     |
| `cmake -DCMAKE_BUILD_TYPE=Release ..`                          | **Downloads CEF** into `build/cef/` (large; needs network).                                                                                                                           |
| `cmake --build . -j$(nproc)`                                   | **Succeeded**; binary at `upstream/linux-wallpaperengine/build/output/linux-wallpaperengine`.                                                                                         |
| `PATH=…/build/output:$PATH` + `./linux-wallpaperengine-gtk.py` | Log shows **`Resolved WPE path: …/linux-wallpaperengine`** (backend discovered).                                                                                                      |

**README changes after this run:** Section “Clone and build the full stack” was rewritten to match the above (no shallow clone warning, json recovery, CEF download note, `-j$(nproc)`, PATH from GTK repo root, `command -v` check).
