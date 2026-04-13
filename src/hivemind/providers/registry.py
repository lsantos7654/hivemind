"""Provider registry and factory.

To add a new provider:
1. Create providers/yourprovider.py with a Provider subclass
2. Add it to PROVIDER_CLASSES below
3. Add provider config to hivemind.json
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hivemind.providers.claude import ClaudeProvider
from hivemind.providers.opencode import OpenCodeProvider

if TYPE_CHECKING:
    from pathlib import Path

    from hivemind.models import ProviderConfig
    from hivemind.providers.base import Provider

PROVIDER_CLASSES: dict[str, type[Provider]] = {
    "claude": ClaudeProvider,
    "opencode": OpenCodeProvider,
}


def get_provider(name: str, provider_config: ProviderConfig, *, providers_dir: Path | None = None) -> Provider:
    """Create a provider instance by name.

    Args:
        name: Provider name (e.g. "claude", "opencode")
        provider_config: Provider configuration model
        providers_dir: Path to the providers directory (for context append lookups)

    Returns:
        Provider instance

    Raises:
        ValueError: If provider name is not recognized
    """
    cls = PROVIDER_CLASSES.get(name)
    if cls is None:
        msg = f"Unknown provider '{name}'. Available: {', '.join(PROVIDER_CLASSES)}"
        raise ValueError(msg)
    return cls(provider_config, providers_dir=providers_dir)
