"""TUI-specific operation wrappers with Textual integration.

These are thin wrappers around :mod:`hivemind.lifecycle` / the body-specific
creator modules that translate structured progress events into Textual
notifications. The post-mutation reload is NOT called from here — it's
registered once as a listener in :mod:`hivemind.tui.app` (``on_mount``).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from hivemind.models import CancellationToken, ProgressInfo, UpdatePhase
from hivemind.tui.models import OperationStatus

if TYPE_CHECKING:
    from collections.abc import Callable

    from hivemind.tui.screens.experts_pane import ExpertsPane
    from hivemind.tui.screens.version_detail_screen import VersionDetailScreen


def create_tui_progress_callback(screen: ExpertsPane, expert_name: str) -> Callable[[ProgressInfo], None]:
    """Create a progress callback that updates the TUI."""

    def on_progress(info: ProgressInfo) -> None:
        if info.phase == UpdatePhase.ANALYZING:
            screen.set_expert_operation_status(expert_name, OperationStatus.IN_PROGRESS)
            screen.set_expert_status_message(expert_name, info.message)
        else:
            screen.set_expert_status_message(expert_name, info.message)

    return on_progress


async def update_expert_async(
    screen: ExpertsPane,
    expert_name: str,
    token: CancellationToken,
    *,
    skip_analysis: bool = False,
) -> None:
    """Async wrapper for refreshing a git-analyzed expert."""
    from hivemind.agents.git_analyzed import update_git_expert

    callback = create_tui_progress_callback(screen, expert_name)

    def on_pid(pid: int) -> None:
        screen.register_subprocess_pid(expert_name, pid)

    try:
        result = await update_git_expert(
            expert_name,
            on_progress=callback,
            on_subprocess_start=on_pid,
            cancellation_token=token,
            skip_analysis=skip_analysis,
        )

        if result.cancelled:
            screen.notify(f"{expert_name}: cancelled", severity="warning")
        elif result.success:
            if result.already_up_to_date:
                screen.notify(
                    f"{expert_name}: already up to date ({result.new_commit[:12]})",
                    severity="information",
                )
            else:
                old_display = result.old_commit[:12] if result.old_commit else "none"
                screen.notify(
                    f"{expert_name}: updated from {old_display} to {result.new_commit[:12]}",
                    severity="information",
                )
        else:
            screen.notify(f"{expert_name}: {result.error}", severity="error")

    except asyncio.CancelledError:
        screen.notify(f"{expert_name}: cancelled by user", severity="warning")
    except Exception as e:
        screen.notify(f"{expert_name}: error - {e}", severity="error")
    finally:
        screen.unregister_worker(expert_name)
        screen.set_expert_operation_status(expert_name, None)
        screen.set_expert_status_message(expert_name, None)


async def enable_expert_async_op(pane: ExpertsPane, expert_name: str) -> None:
    """Async wrapper for enabling an agent from the TUI."""
    from hivemind.lifecycle import enable_agent

    try:
        pane.set_expert_operation_status(expert_name, OperationStatus.IN_PROGRESS)
        pane.set_expert_status_message(expert_name, "enabling...")
        result = await asyncio.to_thread(enable_agent, expert_name)
        if result.success:
            pane.notify(f"Enabled: {expert_name}", severity="information")
        else:
            pane.notify(f"Failed to enable {expert_name}: {result.error}", severity="error")
    except Exception as e:
        pane.notify(f"Error enabling {expert_name}: {e}", severity="error")
    finally:
        pane.set_expert_operation_status(expert_name, None)
        pane.set_expert_status_message(expert_name, None)


async def disable_expert_async_op(pane: ExpertsPane, expert_name: str) -> None:
    """Async wrapper for disabling an agent from the TUI."""
    from hivemind.lifecycle import disable_agent

    try:
        pane.set_expert_operation_status(expert_name, OperationStatus.IN_PROGRESS)
        pane.set_expert_status_message(expert_name, "disabling...")
        result = await asyncio.to_thread(disable_agent, expert_name)
        if result.success:
            pane.notify(f"Disabled: {expert_name}", severity="warning")
        else:
            pane.notify(f"Failed to disable {expert_name}: {result.error}", severity="error")
    except Exception as e:
        pane.notify(f"Error disabling {expert_name}: {e}", severity="error")
    finally:
        pane.set_expert_operation_status(expert_name, None)
        pane.set_expert_status_message(expert_name, None)


async def delete_expert_async_op(pane: ExpertsPane, expert_name: str) -> None:
    """Async wrapper for deleting an agent from the TUI."""
    from hivemind.lifecycle import delete_agent

    try:
        pane.set_expert_operation_status(expert_name, OperationStatus.IN_PROGRESS)
        pane.set_expert_status_message(expert_name, "deleting...")
        result = await asyncio.to_thread(delete_agent, expert_name)
        if result.success:
            pane.notify(f"Deleted: {expert_name}", severity="information")
        else:
            pane.notify(f"Failed to delete {expert_name}: {result.error}", severity="error")
    except Exception as e:
        pane.notify(f"Error deleting {expert_name}: {e}", severity="error")
    finally:
        pane.set_expert_operation_status(expert_name, None)
        pane.set_expert_status_message(expert_name, None)


async def add_expert_async(pane: ExpertsPane, url: str) -> None:
    """Async wrapper for adding a git-analyzed expert from the TUI."""
    from hivemind.agents.git_analyzed import create_git_expert

    name = url.rstrip("/").split("/")[-1].removesuffix(".git")
    try:
        result = await create_git_expert(name, url)
        if result.success:
            pane.notify(f"Expert '{name}' added (unlisted)", severity="information")
        else:
            pane.notify(f"Failed to add expert: {result.error}", severity="error")
    except Exception as e:
        pane.notify(f"Error: {e}", severity="error")


async def switch_version_async_tui(
    screen: VersionDetailScreen,
    expert_name: str,
    target_commit: str,
    token: CancellationToken,
) -> None:
    """Async wrapper for switching versions from the TUI."""
    from hivemind.agents.git_analyzed import switch_version

    def on_progress(info: ProgressInfo) -> None:
        if hasattr(screen, "set_status_message"):
            screen.set_status_message(info.message)
        screen.notify(info.message, severity="information")

    def on_pid(pid: int) -> None:
        screen.register_subprocess_pid(expert_name, pid)

    try:
        result = await switch_version(
            expert_name,
            target_commit,
            on_progress=on_progress,
            on_subprocess_start=on_pid,
            cancellation_token=token,
        )

        if result.cancelled:
            screen.notify("Version switch cancelled", severity="warning")
        elif result.success:
            if result.already_up_to_date:
                screen.notify(f"Already on {target_commit[:12]}", severity="information")
            else:
                screen.notify(f"Switched to {target_commit[:12]}", severity="information")
                if hasattr(screen, "_load_versions"):
                    screen.expert.commit = target_commit
                    await screen._load_versions()
                    screen._populate_table()
                    if hasattr(screen, "query_one"):
                        try:
                            from textual.widgets import Static

                            header = screen.query_one("#expert-header", Static)
                            header.update(
                                f"Expert: {screen.expert.name}\n"
                                f"Current HEAD: {target_commit[:12]}\n"
                                f"Remote: {screen.expert.remote}"
                            )
                        except Exception:
                            pass
        else:
            screen.notify(f"Failed: {result.error or 'Unknown error'}", severity="error")

    except Exception as e:
        screen.notify(f"Error: {e}", severity="error")
    finally:
        screen.unregister_worker(expert_name)
