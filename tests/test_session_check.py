"""Tests for hooks/session_check.py — reference file staleness detection."""

import datetime
import json
import os
import textwrap

import pytest

# Import the module under test
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from session_check import _parse_last_refreshed, main


@pytest.fixture
def md_file(tmp_path):
    """Create a markdown file with given frontmatter content."""

    def _create(content, name="test.md"):
        p = tmp_path / name
        p.write_text(textwrap.dedent(content))
        return str(p)

    return _create


class TestParseLastRefreshed:
    def test_valid_date(self, md_file):
        path = md_file("""\
            ---
            name: test
            last_refreshed: 2026-03-15
            ---
            # Body
        """)
        date, date_str = _parse_last_refreshed(path)
        assert date == datetime.date(2026, 3, 15)
        assert date_str == "2026-03-15"

    def test_missing_last_refreshed(self, md_file):
        path = md_file("""\
            ---
            name: test
            description: no date here
            ---
            # Body
        """)
        date, date_str = _parse_last_refreshed(path)
        assert date is None
        assert date_str is None

    def test_no_frontmatter(self, md_file):
        path = md_file("# Just a heading\nSome text.\n")
        date, date_str = _parse_last_refreshed(path)
        assert date is None
        assert date_str is None

    def test_empty_file(self, md_file):
        path = md_file("")
        date, date_str = _parse_last_refreshed(path)
        assert date is None
        assert date_str is None

    def test_malformed_date(self, md_file):
        path = md_file("""\
            ---
            last_refreshed: not-a-date
            ---
        """)
        date, date_str = _parse_last_refreshed(path)
        assert date is None
        assert date_str is None

    def test_nonexistent_file(self):
        date, date_str = _parse_last_refreshed("/nonexistent/path.md")
        assert date is None
        assert date_str is None

    def test_date_with_extra_whitespace(self, md_file):
        path = md_file("""\
            ---
            last_refreshed:   2026-01-10
            ---
        """)
        date, date_str = _parse_last_refreshed(path)
        # fromisoformat may or may not handle trailing space; verify graceful behavior
        assert date is None or date == datetime.date(2026, 1, 10)


class TestMain:
    def test_no_plugin_root(self, monkeypatch, capsys):
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_stale_file_detected(self, tmp_path, monkeypatch, capsys):
        refs_dir = tmp_path / "skills" / "review-claude-config" / "references"
        refs_dir.mkdir(parents=True)

        stale_date = (datetime.date.today() - datetime.timedelta(days=120)).isoformat()
        (refs_dir / "old-file.md").write_text(
            f"---\nlast_refreshed: {stale_date}\n---\n# Old\n"
        )

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        main()
        output = json.loads(capsys.readouterr().out.strip())
        ctx = output["hookSpecificOutput"]["additionalContext"]
        assert "old-file.md" in ctx
        assert "120 days ago" in ctx

    def test_fresh_files_no_output(self, tmp_path, monkeypatch, capsys):
        refs_dir = tmp_path / "skills" / "review-claude-config" / "references"
        refs_dir.mkdir(parents=True)

        today = datetime.date.today().isoformat()
        (refs_dir / "fresh.md").write_text(
            f"---\nlast_refreshed: {today}\n---\n# Fresh\n"
        )

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_engineering_baseline_hint(self, tmp_path, monkeypatch, capsys):
        refs_dir = tmp_path / "skills" / "review-claude-config" / "references"
        refs_dir.mkdir(parents=True)

        stale_date = (datetime.date.today() - datetime.timedelta(days=100)).isoformat()
        (refs_dir / "engineering-baseline.md").write_text(
            f"---\nlast_refreshed: {stale_date}\n---\n# Baseline\n"
        )

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        main()
        output = json.loads(capsys.readouterr().out.strip())
        ctx = output["hookSpecificOutput"]["additionalContext"]
        assert "/refresh-engineering-baseline" in ctx

    def test_oldest_stale_file_reported(self, tmp_path, monkeypatch, capsys):
        """When multiple files are stale, only the oldest is reported."""
        refs_dir = tmp_path / "skills" / "review-claude-config" / "references"
        refs_dir.mkdir(parents=True)

        older = (datetime.date.today() - datetime.timedelta(days=200)).isoformat()
        newer_stale = (datetime.date.today() - datetime.timedelta(days=95)).isoformat()

        (refs_dir / "very-old.md").write_text(
            f"---\nlast_refreshed: {older}\n---\n"
        )
        (refs_dir / "slightly-stale.md").write_text(
            f"---\nlast_refreshed: {newer_stale}\n---\n"
        )

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        main()
        output = json.loads(capsys.readouterr().out.strip())
        ctx = output["hookSpecificOutput"]["additionalContext"]
        assert "very-old.md" in ctx
        assert "slightly-stale.md" not in ctx

    def test_empty_refs_dir(self, tmp_path, monkeypatch, capsys):
        refs_dir = tmp_path / "skills" / "review-claude-config" / "references"
        refs_dir.mkdir(parents=True)

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        main()
        assert capsys.readouterr().out.strip() == "{}"
