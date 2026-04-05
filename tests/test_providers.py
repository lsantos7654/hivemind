"""Tests for hivemind.providers — pure string function tests."""

from __future__ import annotations

from hivemind.providers import extract_description, strip_frontmatter


class TestExtractDescription:
    def test_extracts_paragraph_after_heading(self):
        body = "# Expert: Bazel\n\nExpert on Bazel build system.\n\n## Overview"
        assert extract_description(body) == "Expert on Bazel build system."

    def test_handles_empty_string(self):
        assert extract_description("") == ""

    def test_no_heading_returns_empty(self):
        body = "Just body content with no heading."
        assert extract_description(body) == ""

    def test_overview_fallback(self):
        body = "# Expert: Test\n\n## Overview\n\nDescription from overview.\n\n## Details"
        result = extract_description(body)
        assert "Description from overview" in result


class TestStripFrontmatter:
    def test_strips_yaml_frontmatter(self):
        content = "---\nname: test\ntools: [Read]\n---\nBody content here."
        assert strip_frontmatter(content) == "Body content here."

    def test_no_frontmatter(self):
        content = "Just body content."
        assert strip_frontmatter(content) == "Just body content."

    def test_preserves_body_formatting(self):
        content = "---\nname: test\n---\n\nLine 1\n\nLine 2"
        result = strip_frontmatter(content)
        assert "Line 1" in result
        assert "Line 2" in result

    def test_empty_string(self):
        assert strip_frontmatter("") == ""
