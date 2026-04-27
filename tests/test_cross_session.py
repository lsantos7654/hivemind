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


def test_session_fork_forwards_parent_id(fake_http):
    fake_http.next_response = {"id": "ses_new", "parentID": "ses_main", "title": "(fork #1)"}
    result = opencode.session_fork("ses_a", parent_id="ses_main", message_id="msg_x")
    _, body = fake_http.posts[0]
    assert body == {"messageID": "msg_x", "parentID": "ses_main"}
    assert result["id"] == "ses_new"


def test_session_root_walks_parent_chain(fake_http):
    fake_http.script("/session/ses_a", {"id": "ses_a", "parentID": None})
    fake_http.script("/session/ses_b", {"id": "ses_b", "parentID": "ses_a"})
    fake_http.script("/session/ses_c", {"id": "ses_c", "parentID": "ses_b"})
    root = opencode.session_root("ses_c")
    assert root["id"] == "ses_a"


def test_helpers_raise_when_detached(monkeypatch):
    from hivemind import runtime

    monkeypatch.setattr(
        runtime,
        "current_context",
        lambda: runtime.RuntimeContext(mode="detached", server_url=None),
    )
    with pytest.raises(RuntimeError, match="no opencode server"):
        opencode.session_list()


# ---------------------------------------------------------------------------
# MCP handlers
# ---------------------------------------------------------------------------


def test_send_to_main_picks_most_recent_root(fake_http):
    fake_http.script(
        "/session?",
        [
            {"id": "ses_root", "title": "main", "parentID": None, "time": {"updated": 1700}},
        ],
    )
    fake_http.script("/session", [{"id": "ses_root", "title": "main", "parentID": None, "time": {"updated": 1700}}])
    fake_http.script("/inbox", {"sessionID": "ses_root", "queued": False, "depth": 0})
    out = run(mcp_tools._handle_send_to_main("ping"))
    assert "delivered" in out[0].text
    assert "ses_root" in out[0].text
    inbox_url = next(p[0] for p in fake_http.posts if "/inbox" in p[0])
    assert inbox_url.endswith("/session/ses_root/inbox")


def test_send_to_main_errors_when_no_root(fake_http):
    fake_http.script("/session", [])
    out = run(mcp_tools._handle_send_to_main("ping"))
    assert "no root session" in out[0].text


def test_continue_expert_matches_subagent_title(fake_http):
    fake_http.script(
        "/session",
        [
            {"id": "ses_x", "title": "earlier (@expert-foo subagent)", "time": {"updated": 100}},
            {"id": "ses_y", "title": "unrelated", "time": {"updated": 200}},
            {"id": "ses_z", "title": "follow-up (@expert-foo subagent)", "time": {"updated": 300}},
        ],
    )
    fake_http.script("/inbox", {"sessionID": "ses_z", "queued": True, "depth": 1})
    out = run(mcp_tools._handle_continue_expert("expert-foo", "another question"))
    # session_list returns most-recent first by default; opencode handles ordering
    # — our handler picks the first match, so any matching ID is acceptable here.
    assert "expert-foo" in out[0].text
    assert "queued" in out[0].text


def test_continue_expert_errors_when_no_session(fake_http):
    fake_http.script("/session", [{"id": "ses_q", "title": "main", "time": {"updated": 1}}])
    out = run(mcp_tools._handle_continue_expert("expert-bar", "hello"))
    assert "no live session" in out[0].text
    assert "Task(subagent_type='expert-bar'" in out[0].text


def test_fork_session_chains_fork_then_inbox(fake_http):
    fake_http.script("/fork", {"id": "ses_fork", "parentID": "ses_main", "title": "(fork #1)"})
    fake_http.script("/inbox", {"sessionID": "ses_fork", "queued": False, "depth": 0})
    out = run(mcp_tools._handle_fork_session("ses_src", "go", "ses_main", ""))
    assert "ses_fork" in out[0].text
    fork_call = next(p for p in fake_http.posts if "/fork" in p[0])
    assert fork_call[1] == {"parentID": "ses_main"}
    inbox_call = next(p for p in fake_http.posts if "/inbox" in p[0])
    assert inbox_call[0].endswith("/session/ses_fork/inbox")


# ---------------------------------------------------------------------------
# Argument extraction
# ---------------------------------------------------------------------------


def test_extract_args_for_new_tools():
    assert mcp_tools._extract_args("list_sessions", {"roots": True, "limit": 7}) == (True, 7)
    assert mcp_tools._extract_args("send_to_session", {"session_id": "s", "message": "m"}) == ("s", "m")
    assert mcp_tools._extract_args("send_to_main", {"message": "m"}) == ("m",)
    assert mcp_tools._extract_args(
        "fork_session",
        {"session_id": "src", "prompt": "go", "parent_id": "p"},
    ) == ("src", "go", "p", "")
    assert mcp_tools._extract_args("continue_expert", {"name": "x", "message": "y"}) == ("x", "y")
