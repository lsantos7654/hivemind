"""TUI-specific operation wrappers with Textual integration."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from hivemind.config import load_config
from hivemind.experts import delete_expert, disable_expert, enable_expert
from hivemind.models import CancellationToken, ProgressInfo, UpdatePhase
from hivemind.mutations import notify_opencode_reload
from hivemind.tui.models import OperationStatus

if TYPE_CHECKING:
    from collections.abc import Callable

    from hivemind.tui.screens.experts_pane import ExpertsPane
    from hivemind.tui.screens.version_detail_screen import VersionDetailScreen


def create_tui_progress_callback(screen: ExpertsPane, expert_name: str) -> Callable[[ProgressInfo], None]:
    """Create a progress callback that updates the TUI."""

    def on_progress(info: ProgressInfo) -> None:
        # Update operation status in the table
        # Called from async context (main thread), so no need for call_from_thread
        if info.phase == UpdatePhase.ANALYZING:
            screen.set_expert_operation_status(expert_name, OperationStatus.IN_PROGRESS)
            # Use the message directly — it already contains file progress info
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
):
    """Async wrapper for updating an expert with cancellation support."""
    from hivemind.experts import update_expert

    callback = create_tui_progress_callback(screen, expert_name)

    def on_pid(pid: int):
        """Called when subprocess starts."""
        screen.register_subprocess_pid(expert_name, pid)

    try:
        result = await update_expert(
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
                notify_opencode_reload()
        else:
            screen.notify(
                f"{expert_name}: {result.error}",
                severity="error",
            )

    except asyncio.CancelledError:
        screen.notify(f"{expert_name}: cancelled by user", severity="warning")

    except Exception as e:
        screen.notify(f"{expert_name}: error - {e}", severity="error")

    finally:
        screen.unregister_worker(expert_name)
        screen.set_expert_operation_status(expert_name, None)
        screen.set_expert_status_message(expert_name, None)
        screen.app.refresh_experts()


async def enable_expert_async_op(pane: ExpertsPane, expert_name: str) -> None:
    """Async wrapper for enabling an expert in the TUI."""
    try:
        pane.set_expert_operation_status(expert_name, OperationStatus.IN_PROGRESS)
        pane.set_expert_status_message(expert_name, "enabling...")
        config = load_config()
        result = await enable_expert(expert_name, config)
        if result.success:
            notify_opencode_reload()
            if result.already_enabled:
                pane.notify(f"{expert_name}: already enabled", severity="information")
            else:
                pane.notify(f"Enabled: {expert_name}", severity="information")
        else:
            pane.notify(f"Failed to enable {expert_name}: {result.error}", severity="error")
    except Exception as e:
        pane.notify(f"Error enabling {expert_name}: {e}", severity="error")
    finally:
        pane.set_expert_operation_status(expert_name, None)
        pane.set_expert_status_message(expert_name, None)
        pane.app.refresh_experts()


async def disable_expert_async_op(pane: ExpertsPane, expert_name: str) -> None:
    """Async wrapper for disabling an expert in the TUI."""
    try:
        pane.set_expert_operation_status(expert_name, OperationStatus.IN_PROGRESS)
        pane.set_expert_status_message(expert_name, "disabling...")
        config = load_config()
        result = await asyncio.to_thread(disable_expert, expert_name, config)
        if result.success:
            notify_opencode_reload()
            if result.already_disabled:
                pane.notify(f"{expert_name}: already disabled", severity="information")
            else:
                pane.notify(f"Disabled: {expert_name}", severity="warning")
        else:
            pane.notify(f"Failed to disable {expert_name}: {result.error}", severity="error")
    except Exception as e:
        pane.notify(f"Error disabling {expert_name}: {e}", severity="error")
    finally:
        pane.set_expert_operation_status(expert_name, None)
        pane.set_expert_status_message(expert_name, None)
        pane.app.refresh_experts()


async def delete_expert_async_op(pane: ExpertsPane, expert_name: str) -> None:
    """Async wrapper for deleting an expert in the TUI."""
    try:
        pane.set_expert_operation_status(expert_name, OperationStatus.IN_PROGRESS)
        pane.set_expert_status_message(expert_name, "deleting...")
        config = load_config()
        result = await asyncio.to_thread(delete_expert, expert_name, config)
        if result.success:
            notify_opencode_reload()
            pane.notify(f"Deleted: {expert_name}", severity="information")
        else:
            pane.notify(f"Failed to delete {expert_name}: {result.error}", severity="error")
    except Exception as e:
        pane.notify(f"Error deleting {expert_name}: {e}", severity="error")
    finally:
        pane.set_expert_operation_status(expert_name, None)
        pane.set_expert_status_message(expert_name, None)
        pane.app.refresh_experts()


async def add_expert_async(pane: ExpertsPane, url: str) -> None:
    """Async wrapper for adding an expert."""
    from hivemind.experts import add_expert

    name = url.rstrip("/").split("/")[-1].removesuffix(".git")

    try:
        result = await add_expert(name, url)
        if result.success:
            notify_opencode_reload()
            pane.notify(f"Expert '{name}' added successfully", severity="information")
        else:
            pane.notify(f"Failed to add expert: {result.error}", severity="error")
    except Exception as e:
        pane.notify(f"Error: {e}", severity="error")
    finally:
        pane.app.refresh_experts()


async def switch_version_async_tui(
    screen: VersionDetailScreen,
    expert_name: str,
    target_commit: str,
    token: CancellationToken,
):
    """Async wrapper for switching versions with TUI integration."""
    from hivemind.experts import switch_version_async

    # Create progress callback (reuse existing helper approach)
    def on_progress(info: ProgressInfo):
        # Update status message on the detail screen
        if hasattr(screen, "set_status_message"):
            screen.set_status_message(info.message)
        # Notify is already thread-safe in Textual workers
        screen.notify(info.message, severity="information")

    def on_pid(pid: int):
        screen.register_subprocess_pid(expert_name, pid)

    try:
        result = await switch_version_async(
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
                screen.notify(
                    f"Already on {target_commit[:12]}",
                    severity="information",
                )
            else:
                notify_opencode_reload()
                screen.notify(f"Switched to {target_commit[:12]}", severity="information")
                # Refresh the version detail screen to show updated active status
                if hasattr(screen, "_load_versions"):
                    screen.expert.commit = target_commit  # Update expert object
                    await screen._load_versions()
                    screen._populate_table()
                    # Update the expert header to show new HEAD
                    if hasattr(screen, "query_one"):
                        try:
                            from textual.widgets import Static

                            header = screen.query_one("#expert-header", Static)
                            header.update(
                                f"Expert: {screen.expert.name}\n"
                                f"Current HEAD: {target_commit[:12]}\n"
                                f"Remote: {screen.expert.remote}",
                            )
                        except Exception:
                            pass
                # Stay on version detail screen - let user press escape to go back
        else:
            screen.notify(f"Failed: {result.error or 'Unknown error'}", severity="error")

    except Exception as e:
        screen.notify(f"Error: {e}", severity="error")
    finally:
        screen.unregister_worker(expert_name)
        screen.app.refresh_experts()
