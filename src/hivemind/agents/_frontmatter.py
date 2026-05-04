"""Tiny YAML-frontmatter reader shared across agent body strategies.

Used by :mod:`hivemind.agents.user_supplied` to read fields from a
hand-authored agent file, and by :mod:`hivemind.agents.system_templated`
to read fields from a Jinja-rendered agent file. Intentionally minimal
— it does not depend on a YAML parser, so it has no transitive cost
and can't go wrong on edge cases that don't matter here.
"""

from __future__ import annotations

import re

__all__ = ["frontmatter_field"]


_FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*\n", re.DOTALL)


def frontmatter_field(text: str, field: str) -> str | None:
    """Extract a single top-level YAML field from the frontmatter.

    Tolerates simple ``key: value`` entries (no nested structures).
    Multi-line scalar values are not supported — keep the value on one
    line. Returns ``None`` if no frontmatter is present or no matching
    field is found.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    for line in m.group("body").splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        if key.strip() == field:
            return value.strip().strip("'\"")
    return None
