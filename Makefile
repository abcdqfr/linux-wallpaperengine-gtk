# In-repo automation (no GUI / engine binary required).
# True end-to-end (GTK + linux-wallpaperengine + wallpaper assets) is not automated here yet.

.PHONY: help ci test fmt-check

PY := $(shell if [ -x .venv-ci/bin/python ]; then echo .venv-ci/bin/python; else echo python3; fi)

help:
	@echo "Targets:"
	@echo "  make ci        Full local suite: venv, py_compile, pytest tests/, ruff, grep, pre-commit, optional analyzers"
	@echo "  make test      Pytest only (uses .venv-ci if present, else python3 — needs pytest installed)"
	@echo "  make fmt-check Ruff check only (needs ruff)"
	@echo ""
	@echo "There is no Makefile recipe yet for launching the GTK app under Xvfb with a real engine binary."

ci:
	@./scripts/ci-local.sh

test:
	@$(PY) -m pytest tests/ -v

fmt-check:
	@$(PY) -m ruff check linux-wallpaperengine-gtk.py wallpaper_process_probe.py tests/
