"""Tests for hooks/session_check.py — reference file staleness detection."""

import datetime
import json
import os
import textwrap

import pytest

# Import the module under test
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from session_check import _check_research_corpus, _check_stale_references, _parse_last_refreshed, main


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


class TestCheckStaleReferences:
    def test_boundary_90_days_not_stale(self, tmp_path):
        refs_dir = tmp_path / "refs"
        refs_dir.mkdir()
        date_90 = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
        (refs_dir / "old.md").write_text(f"---\nlast_refreshed: {date_90}\n---\n")
        result = _check_stale_references(str(refs_dir), datetime.date.today())
        assert result is None

    def test_boundary_91_days_stale(self, tmp_path):
        refs_dir = tmp_path / "refs"
        refs_dir.mkdir()
        date_91 = (datetime.date.today() - datetime.timedelta(days=91)).isoformat()
        (refs_dir / "stale.md").write_text(f"---\nlast_refreshed: {date_91}\n---\n")
        result = _check_stale_references(str(refs_dir), datetime.date.today())
        assert result is not None
        path, date_str, age = result
        assert "stale.md" in path
        assert age == 91

    def test_no_refs_dir(self, tmp_path):
        nonexistent = str(tmp_path / "does-not-exist")
        result = _check_stale_references(nonexistent, datetime.date.today())
        assert result is None

    def test_files_without_frontmatter(self, tmp_path):
        refs_dir = tmp_path / "refs"
        refs_dir.mkdir()
        (refs_dir / "no-date.md").write_text("# No frontmatter here\n")
        (refs_dir / "no-field.md").write_text("---\nname: test\n---\n")
        result = _check_stale_references(str(refs_dir), datetime.date.today())
        assert result is None


class TestCheckResearchCorpus:
    def test_corpus_with_nested_files(self, tmp_path):
        (tmp_path / "research" / "topic-a").mkdir(parents=True)
        (tmp_path / "research" / "topic-b").mkdir(parents=True)
        (tmp_path / "research" / "topic-a" / "file1.md").write_text("# File 1\n")
        (tmp_path / "research" / "topic-b" / "file2.md").write_text("# File 2\n")
        result = _check_research_corpus(str(tmp_path))
        assert result is not None
        assert "2" in result
        assert "Research corpus" in result

    def test_no_research_dir(self, tmp_path):
        result = _check_research_corpus(str(tmp_path))
        assert result is None

    def test_empty_research_dir(self, tmp_path):
        (tmp_path / "research").mkdir()
        result = _check_research_corpus(str(tmp_path))
        assert result is None


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

    def test_combined_stale_and_corpus(self, tmp_path, monkeypatch, capsys):
        refs_dir = tmp_path / "skills" / "review-claude-config" / "references"
        refs_dir.mkdir(parents=True)
        stale_date = (datetime.date.today() - datetime.timedelta(days=120)).isoformat()
        (refs_dir / "old-ref.md").write_text(f"---\nlast_refreshed: {stale_date}\n---\n")

        (tmp_path / "research" / "topic").mkdir(parents=True)
        (tmp_path / "research" / "topic" / "paper.md").write_text("# Paper\n")

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        main()
        output = json.loads(capsys.readouterr().out.strip())
        ctx = output["hookSpecificOutput"]["additionalContext"]
        assert " | " in ctx
        assert "old-ref.md" in ctx
        assert "Research corpus" in ctx
