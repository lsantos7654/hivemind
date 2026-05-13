"""Tests for the cross-session MCP tools and their HTTP helpers.

The tools sit on top of the running opencode engine's REST API. These
tests mock ``httpx`` and the runtime context so we can exercise the
shape of the requests + the parse path without standing up an actual
engine.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from hivemind import opencode
from hivemind.mcp import tools as mcp_tools


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class _FakeResponse:
    def __init__(self, payload: Any, status: int = 200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            msg = f"HTTP {self.status_code}"
            raise RuntimeError(msg)

    def json(self) -> Any:
        return self._payload


class _FakeHttp:
    """Records GET/POST calls and returns scripted responses."""

    def __init__(self) -> None:
        self.gets: list[tuple[str, dict[str, Any]]] = []
        self.posts: list[tuple[str, Any]] = []
        self.next_response: Any = None
        self.responses_by_path: dict[str, Any] = {}

    def script(self, path_suffix: str, payload: Any) -> None:
        self.responses_by_path[path_suffix] = payload

    def _resolve(self, url: str) -> Any:
        for suffix, payload in self.responses_by_path.items():
            if url.endswith(suffix) or suffix in url:
                return payload
        return self.next_response

    def get(self, url: str, *, params=None, timeout=None) -> _FakeResponse:
        self.gets.append((url, params or {}))
        return _FakeResponse(self._resolve(url))

    def post(self, url: str, *, json=None, timeout=None) -> _FakeResponse:
        self.posts.append((url, json))
        return _FakeResponse(self._resolve(url))


@pytest.fixture
def fake_http(monkeypatch):
    fake = _FakeHttp()
    monkeypatch.setattr(opencode.httpx, "get", fake.get)
    monkeypatch.setattr(opencode.httpx, "post", fake.post)

    from hivemind import runtime

    monkeypatch.setattr(
        runtime,
        "current_context",
        lambda: runtime.RuntimeContext(mode="attached", server_url="http://localhost:9999"),
    )
    return fake


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def test_session_list_returns_payload(fake_http):
    fake_http.next_response = [
        {"id": "ses_a", "title": "main", "parentID": None, "time": {"updated": 1}},
        {"id": "ses_b", "title": "child", "parentID": "ses_a", "time": {"updated": 2}},
    ]
    out = opencode.session_list(roots=True, limit=5)
    assert len(out) == 2
    assert fake_http.gets[0][0].endswith("/session")
    assert fake_http.gets[0][1]["roots"] == "true"
    assert fake_http.gets[0][1]["limit"] == "5"


def test_session_inbox_posts_text_part(fake_http):
    fake_http.next_response = {"sessionID": "ses_a", "queued": True, "depth": 1}
    result = opencode.session_inbox("ses_a", "hello there")
    url, body = fake_http.posts[0]
    assert url.endswith("/session/ses_a/inbox")
    assert body == {"parts": [{"type": "text", "text": "hello there"}]}
    assert result["queued"] is True


def test_helpers_raise_when_detached(monkeypatch):
    from hivemind import runtime

    monkeypatch.setattr(
        runtime,
        "current_context",
        lambda: runtime.RuntimeContext(mode="detached", server_url=None),
    )
    with pytest.raises(RuntimeError, match="no opencode server"):
        opencode.session_list()


def test_live_session_ids_returns_set(fake_http):
    fake_http.script("/global/live-sessions", {"sessions": ["ses_a", "ses_b"]})
    result = opencode.live_session_ids()
    assert result == {"ses_a", "ses_b"}


def test_background_tasks_active_returns_list(fake_http):
    fake_http.script(
        "/global/background-tasks",
        {
            "tasks": [
                {"parentID": "ses_root", "taskID": "ses_bg1", "status": "running"},
                {"parentID": "ses_root", "taskID": "ses_bg2", "status": "complete"},
            ],
        },
    )
    result = opencode.background_tasks_active()
    assert len(result) == 2
    running = [t for t in result if t["status"] == "running"]
    complete = [t for t in result if t["status"] == "complete"]
    assert running[0]["taskID"] == "ses_bg1"
    assert complete[0]["taskID"] == "ses_bg2"
    # Endpoint shape — matches the dep_patch SDK addition.
    assert any(url.endswith("/global/background-tasks") for url, _ in fake_http.gets)


def test_background_tasks_active_returns_empty_when_idle(fake_http):
    fake_http.script("/global/background-tasks", {"tasks": []})
    assert opencode.background_tasks_active() == []


# ---------------------------------------------------------------------------
# send_message
# ---------------------------------------------------------------------------


def test_send_message_delivers_to_inbox(fake_http):
    fake_http.next_response = {"sessionID": "ses_a", "queued": False, "depth": 0}
    out = run(mcp_tools._handle_send_message("ses_a", "hello"))
    url, body = fake_http.posts[0]
    assert url.endswith("/session/ses_a/inbox")
    assert body == {"parts": [{"type": "text", "text": "hello"}]}
    assert "delivered" in out[0].text


def test_send_message_reports_queued_when_busy(fake_http):
    fake_http.next_response = {"sessionID": "ses_a", "queued": True, "depth": 3}
    out = run(mcp_tools._handle_send_message("ses_a", "hello"))
    assert "queued" in out[0].text
    assert "depth: 3" in out[0].text


# ---------------------------------------------------------------------------
# list_sessions
# ---------------------------------------------------------------------------


def test_list_sessions_live_only_filters_out_unattached(fake_http):
    fake_http.script("/global/live-sessions", {"sessions": ["ses_live"]})
    fake_http.script(
        "/session",
        [
            {"id": "ses_live", "title": "active", "parentID": None, "time": {"updated": 200}},
            {"id": "ses_dead", "title": "stale", "parentID": None, "time": {"updated": 100}},
        ],
    )
    out = run(mcp_tools._handle_list_sessions(True, False, False, 50))
    payload = out[0].text
    assert "ses_live" in payload
    assert "ses_dead" not in payload


def test_list_sessions_includes_subagents_under_live_parent(fake_http):
    fake_http.script("/global/live-sessions", {"sessions": ["ses_root"]})
    fake_http.script(
        "/session",
        [
            {"id": "ses_root", "title": "root", "parentID": None, "time": {"updated": 100}},
            {"id": "ses_child", "title": "@expert-x subagent", "parentID": "ses_root", "time": {"updated": 110}},
            {"id": "ses_grandchild", "title": "deeper", "parentID": "ses_child", "time": {"updated": 120}},
            {"id": "ses_orphan", "title": "stale orphan", "parentID": None, "time": {"updated": 50}},
        ],
    )
    out = run(mcp_tools._handle_list_sessions(True, False, False, 50))
    payload = out[0].text
    assert "ses_root" in payload
    assert "ses_child" in payload
    assert "ses_grandchild" in payload
    assert "ses_orphan" not in payload


def test_list_sessions_tree_nests_children(fake_http):
    fake_http.script("/global/live-sessions", {"sessions": ["ses_root"]})
    fake_http.script(
        "/session",
        [
            {"id": "ses_root", "title": "root", "parentID": None, "time": {"updated": 100}},
            {"id": "ses_child", "title": "child", "parentID": "ses_root", "time": {"updated": 110}},
        ],
    )
    out = run(mcp_tools._handle_list_sessions(True, True, False, 50))
    import json as _json

    parsed = _json.loads(out[0].text)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["id"] == "ses_root"
    assert len(parsed[0]["children"]) == 1
    assert parsed[0]["children"][0]["id"] == "ses_child"


def test_list_sessions_live_only_false_skips_filter(fake_http):
    fake_http.script(
        "/session",
        [
            {"id": "ses_a", "title": "a", "parentID": None, "time": {"updated": 1}},
            {"id": "ses_b", "title": "b", "parentID": None, "time": {"updated": 2}},
        ],
    )
    out = run(mcp_tools._handle_list_sessions(False, False, False, 50))
    assert "ses_a" in out[0].text
    assert "ses_b" in out[0].text
    # No /global/live-sessions call should be made when live_only=False.
    assert all("/global/live-sessions" not in url for url, _ in fake_http.gets)


# ---------------------------------------------------------------------------
# Argument extraction
# ---------------------------------------------------------------------------


def test_extract_args_for_cross_session_tools():
    assert mcp_tools._extract_args("list_sessions", {"roots": True, "limit": 7}) == (
        True,
        False,
        True,
        7,
    )
    assert mcp_tools._extract_args(
        "list_sessions",
        {"live_only": False, "tree": True, "limit": 100},
    ) == (False, True, False, 100)
    assert mcp_tools._extract_args("send_message", {"session_id": "s", "message": "m"}) == ("s", "m")


def test_extract_args_for_renamed_update_agent():
    """prep_update_agent / finalize_update_agent replaced the old update_agent."""
    assert mcp_tools._extract_args("prep_update_agent", {"name": "expert-foo"}) == ("expert-foo",)
    assert mcp_tools._extract_args("finalize_update_agent", {"name": "expert-foo"}) == ("expert-foo",)


def test_dispatcher_does_not_expose_dropped_tools():
    # Sanity: the deprecated tools must not be registered.
    for dropped in (
        "send_to_session",
        "send_to_main",
        "fork_session",
        "query_session_fork",
        "continue_expert",
        "get_knowledge",
        "search_knowledge",
        "refresh_agent",
    ):
        assert dropped not in mcp_tools.TOOL_HANDLERS, f"{dropped} should be removed"
        assert dropped not in mcp_tools._ARG_EXTRACTORS, f"{dropped} should be removed"
