"""Tests for opencode string helpers (moved from hivemind.provider)."""

from __future__ import annotations

from hivemind.opencode import extract_description, strip_frontmatter, yaml_escape_double_quoted


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


class TestYamlEscapeDoubleQuoted:
    def test_no_special_chars(self):
        assert yaml_escape_double_quoted("plain text") == "plain text"

    def test_escapes_double_quotes(self):
        assert yaml_escape_double_quoted('the "foo" bar') == 'the \\"foo\\" bar'

    def test_escapes_backslashes(self):
        assert yaml_escape_double_quoted("back\\slash") == "back\\\\slash"

    def test_escapes_both(self):
        assert yaml_escape_double_quoted('a\\"b') == 'a\\\\\\"b'

    def test_empty_string(self):
        assert yaml_escape_double_quoted("") == ""

    def test_result_is_valid_yaml(self):
        """Escaped description round-trips through a YAML parser."""
        import yaml

        raw = 'Expert on the Click repository \u2014 the "Command Line Interface Creation Kit" for Python.'
        escaped = yaml_escape_double_quoted(raw)
        doc = f'description: "{escaped}"'
        parsed = yaml.safe_load(doc)
        assert parsed["description"] == raw

    def test_real_world_impersonate(self):
        """Descriptions with impersonate=\"chrome\" survive YAML parsing."""
        import yaml

        raw = 'configuring impersonation targets (`impersonate="chrome"`, `impersonate="safari_ios"`)'
        escaped = yaml_escape_double_quoted(raw)
        doc = f'description: "{escaped}"'
        parsed = yaml.safe_load(doc)
        assert parsed["description"] == raw
