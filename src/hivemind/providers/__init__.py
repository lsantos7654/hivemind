"""Provider abstraction for multi-platform AI coding agent support.

Re-exports public API so callers can continue using ``from hivemind.providers import ...``.
"""

from hivemind.providers.base import Provider, extract_description, replace_expert_paths, strip_frontmatter
from hivemind.providers.registry import PROVIDER_CLASSES, get_provider

__all__ = [
    "PROVIDER_CLASSES",
    "Provider",
    "extract_description",
    "get_provider",
    "replace_expert_paths",
    "strip_frontmatter",
]
