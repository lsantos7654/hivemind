SHELL := /bin/bash

.PHONY: help install update test clean engine dev dev-save dev-reset

BAZELISK ?= bazelisk
LAUNCHER := $(HOME)/.local/bin/hivemind

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# User-facing targets
# ---------------------------------------------------------------------------

help: ## Show this help.
	@printf "Hivemind — Bazel-native build for the Python CLI + bundled opencode engine.\n\n"
	@printf "Usage: make <target>\n\n"
	@printf "Targets:\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@printf "\nFirst-time setup: \033[36mmake install\033[0m  (bazelisk is the only required system dep)\n"

install: ## Build hivemind and write a launcher wrapper into ~/.local/bin/.
	@command -v $(BAZELISK) >/dev/null || { \
	  echo "ERROR: bazelisk required. brew install bazelisk"; exit 1; }
	$(BAZELISK) build //:hivemind
	@mkdir -p $(HOME)/.local/bin
	@# Resolve the launcher via cquery, not the workspace bazel-bin/ symlink.
	@# rules_py applies a configuration transition, so the binary lives at
	@# bazel-out/<cfg>-ST-<hash>/bin/... — and the workspace bazel-bin/ symlink
	@# can rotate between transitioned and un-transitioned dirs depending on
	@# what was last built. cquery gives us the exact file path for this
	@# specific target. The wrapper sets RUNFILES_DIR explicitly so the
	@# launcher's runfiles initializer doesn't try to look next to the wrapper.
	@execroot=$$($(BAZELISK) info execution_root 2>/dev/null); \
	 relpath=$$($(BAZELISK) cquery --output=files //:hivemind 2>/dev/null | grep -E '/hivemind$$' | head -1); \
	 launcher="$$execroot/$$relpath"; \
	 rm -f $(LAUNCHER); \
	 printf '#!/usr/bin/env bash\nLAUNCHER=%q\nexec env RUNFILES_DIR="$${LAUNCHER}.runfiles" "$$LAUNCHER" "$$@"\n' "$$launcher" > $(LAUNCHER); \
	 chmod +x $(LAUNCHER)
	@echo ""
	@echo "✓ Installed: $(LAUNCHER)"
	@echo "  (Make sure ~/.local/bin is on your PATH.)"

update: ## Pull, rebuild, refresh launcher (binary refreshes; Python source is live via runfiles).
	$(MAKE) install

engine: ## Rebuild only the bun-compiled engine.
	$(BAZELISK) build //:engine

test: ## Run the full Bazel test suite (Python tests + bun/engine smoke tests).
	$(BAZELISK) test //...

clean: ## Clean Bazel outputs and remove the launcher symlink.
	$(BAZELISK) clean
	rm -f $(LAUNCHER)

# ---------------------------------------------------------------------------
# Patch dev workflow — clone opencode into dev/, edit, save patches.
# See scripts/dev-opencode.py for details.
# ---------------------------------------------------------------------------

dev: ## Clone opencode into dev/opencode and apply patches as commits.
	@python3 scripts/dev-opencode.py clone

dev-save: ## Regenerate third_party/patches/*.patch from dev/opencode commits.
	@python3 scripts/dev-opencode.py save

dev-reset: ## Wipe dev/opencode and re-clone from scratch.
	rm -rf dev/opencode
	@python3 scripts/dev-opencode.py clone
