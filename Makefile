# In-repo automation (no GUI / engine binary required).
# True end-to-end (GTK + linux-wallpaperengine + wallpaper assets) is not automated here yet.

.PHONY: help ci test fmt-check

PY := $(shell if [ -x .venv-ci/bin/python ]; then echo .venv-ci/bin/python; else echo python3; fi)

help:
	@echo "Targets:"
	@echo "  make ci        venv + pre-commit --all-files (byte-compile, pytest, ruff, black, …) + optional analyzers"
	@echo "  make test      Pytest only (uses .venv-ci if present, else python3 — needs pytest installed)"
	@echo "  make fmt-check Ruff check only (needs ruff)"
	@echo ""
	@echo "Install hooks once:  .venv-ci/bin/pre-commit install"
	@echo "No Makefile recipe yet for Xvfb + real linux-wallpaperengine binary E2E."

ci:
	@./scripts/ci-local.sh

test:
	@$(PY) -m pytest tests/ -v

fmt-check:
	@$(PY) -m ruff check linux-wallpaperengine-gtk.py wallpaper_process_probe.py tests/
