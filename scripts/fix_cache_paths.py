#!/usr/bin/env python3
"""One-time fixup: replace hardcoded ~/.cache/hivemind with {CACHE_DIR} placeholder.

Many AI-generated agent.md files baked in literal ~/.cache/hivemind paths
instead of using the {CACHE_DIR} template placeholder. This script normalizes
them so the deploy pipeline can expand to absolute paths at deploy time.

Usage:
    python scripts/fix_cache_paths.py          # dry-run (shows what would change)
    python scripts/fix_cache_paths.py --apply  # write changes
"""

from __future__ import annotations

import sys
from pathlib import Path

EXPERTS_DIR = Path(__file__).resolve().parent.parent / "experts"
OLD = "~/.cache/hivemind"
NEW = "{CACHE_DIR}"


def main() -> None:
    apply = "--apply" in sys.argv

    agent_files = sorted(EXPERTS_DIR.glob("*/HEAD/agent.md"))
    changed = 0

    for path in agent_files:
        resolved = path.resolve()
        if not resolved.exists():
            continue

        content = resolved.read_text()
        if OLD not in content:
            continue

        updated = content.replace(OLD, NEW)
        expert_name = path.parts[-3]  # experts/<name>/HEAD/agent.md
        count = content.count(OLD)
        print(f"  {expert_name}: {count} occurrence(s)")

        if apply:
            resolved.write_text(updated)

        changed += 1

    print()
    if changed == 0:
        print("No files need updating.")
    elif apply:
        print(f"Updated {changed} file(s).")
    else:
        print(f"{changed} file(s) would be updated. Run with --apply to write changes.")


if __name__ == "__main__":
    main()
