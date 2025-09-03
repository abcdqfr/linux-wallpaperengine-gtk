.PHONY: help install test build clean monolith dev-setup

help: ## Show this help message
	@echo "Linux Wallpaper Engine GTK - Development Commands"
	@echo "================================================"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	pip install -e .

test: ## Run tests
	pytest tests/ -v

build: ## Build the package
	python -m build

monolith: ## Build standalone monolith for distribution
	python3 scripts/build_monolith.py

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -f linux-wallpaperengine-gtk-standalone.py

dev-setup: ## Set up development environment
	pip install -e ".[dev]"
	pre-commit install

format: ## Format code with ruff
	ruff format src/ tests/

lint: ## Lint code with ruff
	ruff check src/ tests/

check: format lint test ## Run all checks (format, lint, test)

release: check build monolith ## Prepare release (checks, build, monolith)
	@echo "✅ Release ready!"
	@echo "📦 Package: dist/"
	@echo "🚀 Monolith: linux-wallpaperengine-gtk-standalone.py"
