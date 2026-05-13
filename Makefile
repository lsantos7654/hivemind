SHELL := /bin/bash

.PHONY: help install update test unit lint typecheck engine-test format \
        coverage coverage-serve engine clean dev dev-save dev-reset

BAZELISK ?= bazelisk
LAUNCHER := $(HOME)/.local/bin/hivemind

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# User-facing targets — every action wraps `bazelisk`. Direct invocations
# of pytest, bun, ruff, mypy, tsgo, buildifier, or pre-commit are
# intentionally absent: Bazel is the universal entry point. (Stage 0 of
# docs/TESTING_ROADMAP.md.)
# ---------------------------------------------------------------------------

help: ## Show this help.
	@printf "Hivemind — Bazel-native build for the Python CLI + bundled opencode engine.\n\n"
	@printf "Usage: make <target>\n\n"
	@printf "Targets:\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / { printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@printf "\nFirst-time setup: \033[36mmake install\033[0m  (bazelisk is the only required system dep)\n"

install: ## Build hivemind + engine and write a launcher wrapper into ~/.local/bin/.
	@command -v $(BAZELISK) >/dev/null || { \
	  echo "ERROR: bazelisk required. brew install bazelisk"; exit 1; }
	$(BAZELISK) build //:hivemind //:engine
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

# ---------------------------------------------------------------------------
# Test / quality-gate targets
# ---------------------------------------------------------------------------

test: ## Run every Bazel test (unit + lint + typecheck + engine + smoke).
	$(BAZELISK) test //... '@opencode_src//...'

unit: ## Run only Python pytest targets.
	$(BAZELISK) test //... --test_tag_filters=unit

lint: ## Run ruff + buildifier.
	$(BAZELISK) test //... --test_tag_filters=lint

typecheck: ## Run mypy on Python; tsgo on engine (engine excluded by default — `manual` tag pending Stage 6).
	$(BAZELISK) test //... --test_tag_filters=typecheck

engine-test: ## Run every engine bun:test target (~155 targets).
	$(BAZELISK) test '@opencode_src//...' --test_tag_filters=engine

format: ## Apply ruff format + buildifier fix + ruff check --fix in place.
	$(BAZELISK) run //tools/bazel:format

coverage: ## Run all tests with coverage instrumentation, generate HTML.
	$(BAZELISK) coverage --combined_report=lcov --instrumentation_filter='^//' \
		//tests:test_core //tests:test_provider //tests:test_cross_session \
		//tests:test_memory_daemon //tests:test_ephemeral_invariants \
		'@opencode_src//...' --test_tag_filters=engine
	rm -rf tools/coverage/coverage_output/htmlcov
	mkdir -p tools/coverage/coverage_output/htmlcov
	genhtml -o tools/coverage/coverage_output/htmlcov \
		--title "Hivemind Coverage" \
		--ignore-errors inconsistent,corrupt,source \
		--synthesize-missing \
		"$$($(BAZELISK) info output_path)/_coverage/_coverage_report.dat"
	@echo "Report: tools/coverage/coverage_output/htmlcov/index.html"
	@echo "  open tools/coverage/coverage_output/htmlcov/index.html"
	@echo "  or: make coverage-serve  →  http://localhost:8080/"

coverage-serve: ## Serve the coverage report at http://localhost:8080/.
	@echo "Serving at http://localhost:8080/"
	@cd tools/coverage/coverage_output/htmlcov && python3 -m http.server 8080

engine: ## Rebuild only the bun-compiled engine.
	$(BAZELISK) build //:engine

clean: ## Clean Bazel outputs and remove the launcher symlink.
	$(BAZELISK) clean
	rm -f $(LAUNCHER)

# ---------------------------------------------------------------------------
# Patch dev workflow — clone opencode into dev/, edit, save patches.
# See scripts/dev-opencode.py for details. These are the ONLY targets
# that shell out (to a Python helper script) — everything else wraps
# bazelisk.
# ---------------------------------------------------------------------------

dev: ## Clone opencode into dev/opencode and apply patches as commits.
	@python3 scripts/dev-opencode.py clone

dev-save: ## Regenerate third_party/patches/*.patch from dev/opencode commits.
	@python3 scripts/dev-opencode.py save
	@# `_rewrite_patches_list` adds new entries to the list and may
	@# leave whitespace drift that buildifier wants normalized. Run
	@# fix-mode so `make lint` after `make dev-save` stays green.
	$(BAZELISK) run //tools/bazel:buildifier_fix

dev-reset: ## Wipe dev/opencode and re-clone from scratch.
	rm -rf dev/opencode
	@python3 scripts/dev-opencode.py clone
