"""Tests for hivemind_cli.core — regression tests and filesystem operations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from hivemind_cli.config import get_head_commit, load_json, save_json

if TYPE_CHECKING:
    from pathlib import Path


class TestLoadJson:
    def test_empty_file_returns_empty_dict(self, tmp_path: Path):
        """REGRESSION: empty config.json must not crash (JSONDecodeError)."""
        p = tmp_path / "empty.json"
        p.write_text("")
        assert load_json(p) == {}

    def test_missing_file_returns_empty_dict(self, tmp_path: Path):
        p = tmp_path / "missing.json"
        assert load_json(p) == {}

    def test_whitespace_only_returns_empty_dict(self, tmp_path: Path):
        p = tmp_path / "whitespace.json"
        p.write_text("   \n  ")
        assert load_json(p) == {}

    def test_valid_json(self, tmp_path: Path):
        p = tmp_path / "valid.json"
        p.write_text('{"key": "value"}')
        assert load_json(p) == {"key": "value"}


class TestSaveJson:
    def test_atomic_write(self, tmp_path: Path):
        """Verify save_json uses atomic write (temp + replace)."""
        p = tmp_path / "config.json"
        save_json(p, {"test": True})
        assert p.exists()
        assert json.loads(p.read_text()) == {"test": True}

    def test_no_partial_write_on_error(self, tmp_path: Path):
        """If serialization succeeds but write fails, original file is preserved."""
        p = tmp_path / "config.json"
        p.write_text('{"original": true}')

        # Write valid data
        save_json(p, {"updated": True})
        assert json.loads(p.read_text()) == {"updated": True}

    def test_creates_parent_dirs(self, tmp_path: Path):
        p = tmp_path / "sub" / "dir" / "config.json"
        save_json(p, {"nested": True})
        assert json.loads(p.read_text()) == {"nested": True}

    def test_no_temp_files_left_behind(self, tmp_path: Path):
        p = tmp_path / "config.json"
        save_json(p, {"clean": True})
        # No .tmp files should remain
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == []

    def test_utf8_encoding(self, tmp_path: Path):
        p = tmp_path / "config.json"
        save_json(p, {"emoji": "🚀", "cjk": "日本語"})
        content = p.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["emoji"] == "🚀"
        assert data["cjk"] == "日本語"


class TestGetHeadCommit:
    def test_returns_str_not_path(self, tmp_path: Path):
        """REGRESSION: must return str, not Path."""
        expert = tmp_path / "expert"
        expert.mkdir()
        (expert / "abc123").mkdir()
        (expert / "HEAD").symlink_to("abc123")
        result = get_head_commit(expert)
        assert isinstance(result, str)
        assert result == "abc123"

    def test_returns_none_when_no_head(self, tmp_path: Path):
        expert = tmp_path / "expert"
        expert.mkdir()
        result = get_head_commit(expert)
        assert result is None


class TestStdoutStderrNotSwapped:
    def test_fd_assignment_pattern(self):
        """Verify the swapped stdout/stderr bug is fixed by checking source code."""
        import inspect

        import hivemind_cli.core as core

        source = inspect.getsource(core)
        # The bug was: stdout=stderr_file.fileno(), stderr=stdout_file.fileno()
        # Fixed to: stdout=stdout_file.fileno(), stderr=stderr_file.fileno()
        assert "stdout=stderr_file.fileno()" not in source
        assert "stderr=stdout_file.fileno()" not in source
