"""``SystemTemplatedBody`` — body strategy for hivemind-managed worker agents.

Catalog entries of this kind are deployed by rendering a Jinja template
under ``src/hivemind/templates/``. There is no backing repo, no roster,
no AI analysis, and no user-authored markdown file — the template is
the source of truth and ``hivemind sync`` regenerates the deployed
agent body.

Used today for ``hivemind-expert-curator`` (the orchestrator-spawned
subagent that performs in-session analysis as the no-MCP-timeout path
for adding new git-analyzed experts). Future system agents (e.g. a
memory-compaction daemon) can drop in the same way: author a template
under ``templates/agents/`` and seed the catalog entry from
    ``lifecycle.sync_workspace``.

System-templated agents are stateless workers — ``memory_enabled``
returns ``False``, so ``Agent.deploy`` skips both the memory-tree
scaffold and the memory-section append.
"""

from __future__ import annotations

from typing import Any

from hivemind.agents._frontmatter import frontmatter_field
from hivemind.models import SystemTemplatedParams
from hivemind.templates import render

__all__ = ["SystemTemplatedBody"]


class SystemTemplatedBody:
    """Body strategy for hivemind-managed Jinja-templated worker agents."""

    kind: str = "system_templated"

    def __init__(self, name: str, params: SystemTemplatedParams) -> None:
        self.name = name
        self.params = params

    # --- catalog (de)serialisation -----------------------------------------

    @classmethod
    def from_catalog(cls, name: str, params: dict[str, Any]) -> SystemTemplatedBody:
        return cls(name=name, params=SystemTemplatedParams.model_validate(params))

    def to_catalog(self) -> dict[str, Any]:
        return self.params.model_dump()

    # --- body protocol -----------------------------------------------------

    def render(self) -> str:
        """Render the template with model config injected from config.json.

        System-templated agents pass through their frontmatter verbatim,
        so model / small_model are injected as Jinja variables. If either
        is unset the render raises (StrictUndefined).
        """
        from hivemind.opencode import _app_cfg

        app = _app_cfg()
        return render(self.params.template, model=app.model, small_model=app.small_model)

    def description(self) -> str:
        """Pull ``description`` out of the rendered template's frontmatter."""
        return frontmatter_field(self.render(), "description") or ""

    def librarian_entry(self) -> str:
        desc = self.description() or "(no description)"
        return (
            f"### {self.name}\n"
            f"Hivemind-internal worker agent. {desc}\n"
            f"Source: ``src/hivemind/templates/{self.params.template}`` "
            f"(re-rendered on ``hivemind sync``)."
        )

    def memory_enabled(self) -> bool:
        """System workers are stateless; no memory tree, no memory section."""
        return False

    def on_deploy(self) -> None:
        # No backing dir to symlink, no repo to clone. The agent file
        # written by Agent.deploy() is the entire deployment.
        pass

    def on_undeploy(self) -> None:
        pass

    def on_delete(self) -> None:
        # The template lives in source — nothing on disk to remove.
        pass
