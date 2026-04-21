SHELL := /bin/bash

.PHONY: help install uninstall update test python-tests clean engine

BAZELISK   ?= bazelisk
BUNDLE_DIR := src/hivemind/_bundled
ENGINE     := $(BUNDLE_DIR)/hivemind-engine

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# User-facing targets
# ---------------------------------------------------------------------------

help: ## Show this help.
	@printf "Hivemind — Bazel-native build for the Python CLI + bundled opencode engine.\n\n"
	@printf "Usage: make <target>\n\n"
	@printf "Targets:\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / { printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@printf "\nFirst-time setup: \033[36mmake install\033[0m\n"

install: $(ENGINE) ## Build the bundled engine and install the hivemind CLI via uv.
	@command -v uv >/dev/null || { echo "ERROR: uv required."; exit 1; }
	uv tool install --reinstall --force --editable .
	@echo ""
	@echo "✓ hivemind installed. The bundled engine is at $(ENGINE)."
	@echo "  Try: hivemind --help"

uninstall: ## Remove the hivemind CLI and the bundled engine binary.
	-uv tool uninstall hivemind 2>/dev/null
	rm -f $(ENGINE)

update: ## Force-rebuild the engine and reinstall the CLI.
	rm -f $(ENGINE)
	$(MAKE) install

engine: $(ENGINE) ## Rebuild only the engine (no Python install).

test: python-tests ## Run the full test suite (uv pytest + bazel test //...).
	$(BAZELISK) test //...

python-tests: ## Run only the Python pytest suite via uv.
	uv run pytest

clean: ## Clean Bazel outputs and remove the bundled engine.
	$(BAZELISK) clean
	rm -f $(ENGINE)

# ---------------------------------------------------------------------------
# Internal targets
# ---------------------------------------------------------------------------

# Build the engine via Bazel and copy it into the Python package so that
# `uv tool install -e .` finds it via importlib.resources at import time.
#
# The cquery output is execroot-relative (e.g. external/.../hivemind-engine),
# so we prefix it with the execution_root reported by `bazel info`.
$(ENGINE):
	@command -v $(BAZELISK) >/dev/null || { \
	  echo "ERROR: bazelisk required. Install with: brew install bazelisk"; \
	  exit 1; }
	$(BAZELISK) build //:engine
	@mkdir -p $(BUNDLE_DIR)
	@execroot=$$($(BAZELISK) info execution_root 2>/dev/null); \
	relpath=$$($(BAZELISK) cquery --output=files //:engine 2>/dev/null); \
	cp -f "$$execroot/$$relpath" $(ENGINE)
	chmod +x $(ENGINE)
