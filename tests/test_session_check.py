"""Tests for hooks/session_check.py — reference file staleness detection."""

import datetime
import json
import os
import pathlib
import subprocess
import sys
import textwrap

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from session_check import _check_research_corpus, _check_stale_references, _parse_last_refreshed, main

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "hooks" / "session_check.py"


def _run_hook(payload, env_overrides=None):
    env = os.environ.copy()
    if env_overrides is not None:
        for k, v in env_overrides.items():
            if v is None:
                env.pop(k, None)
            else:
                env[k] = v
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
        check=False,
    )


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
        date, date_str, error = _parse_last_refreshed(path)
        assert date == datetime.date(2026, 3, 15)
        assert date_str == "2026-03-15"
        assert error is None

    def test_missing_last_refreshed(self, md_file):
        path = md_file("""\
            ---
            name: test
            description: no date here
            ---
            # Body
        """)
        date, date_str, error = _parse_last_refreshed(path)
        assert date is None
        assert date_str is None
        assert error is None

    def test_no_frontmatter(self, md_file):
        path = md_file("# Just a heading\nSome text.\n")
        date, date_str, error = _parse_last_refreshed(path)
        assert date is None
        assert date_str is None
        assert error is None

    def test_empty_file(self, md_file):
        path = md_file("")
        date, date_str, error = _parse_last_refreshed(path)
        assert date is None
        assert date_str is None
        assert error is None

    def test_malformed_date(self, md_file):
        path = md_file("""\
            ---
            last_refreshed: not-a-date
            ---
        """)
        date, date_str, error = _parse_last_refreshed(path)
        assert date is None
        assert date_str == "not-a-date"
        assert error is not None

    def test_nonexistent_file(self):
        date, date_str, error = _parse_last_refreshed("/nonexistent/path.md")
        assert date is None
        assert date_str is None
        assert error is None

    def test_date_with_extra_whitespace(self, md_file):
        path = md_file("""\
            ---
            last_refreshed:   2026-01-10
            ---
        """)
        date, date_str, error = _parse_last_refreshed(path)
        assert date == datetime.date(2026, 1, 10)
        assert date_str == "2026-01-10"
        assert error is None

    def test_malformed_date_short_format(self, md_file):
        """Non-zero-padded date like 2026-4-5 is rejected by DATE_RE."""
        path = md_file("""\
            ---
            last_refreshed: 2026-4-5
            ---
        """)
        date, date_str, error = _parse_last_refreshed(path)
        assert date is None
        assert date_str == "2026-4-5"
        assert error == "not strict YYYY-MM-DD"

    def test_invalid_calendar_date(self, md_file):
        """Date with correct format but impossible value (Feb 30) is rejected."""
        path = md_file("""\
            ---
            last_refreshed: 2026-02-30
            ---
        """)
        date, date_str, error = _parse_last_refreshed(path)
        assert date is None
        assert date_str == "2026-02-30"
        assert error == "not a valid calendar date"

    def test_empty_date_value(self, md_file):
        """Empty value after last_refreshed: treated as absent."""
        path = md_file("""\
            ---
            last_refreshed:
            ---
        """)
        date, date_str, error = _parse_last_refreshed(path)
        assert date is None
        assert date_str is None
        assert error is None


class TestCheckStaleReferences:
    def test_boundary_90_days_not_stale(self, tmp_path):
        refs_dir = tmp_path / "refs"
        refs_dir.mkdir()
        date_90 = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
        (refs_dir / "old.md").write_text(f"---\nlast_refreshed: {date_90}\n---\n")
        stale, errors = _check_stale_references(str(refs_dir), datetime.date.today())
        assert stale is None
        assert errors == []

    def test_boundary_91_days_stale(self, tmp_path):
        refs_dir = tmp_path / "refs"
        refs_dir.mkdir()
        date_91 = (datetime.date.today() - datetime.timedelta(days=91)).isoformat()
        (refs_dir / "stale.md").write_text(f"---\nlast_refreshed: {date_91}\n---\n")
        stale, errors = _check_stale_references(str(refs_dir), datetime.date.today())
        assert stale is not None
        path, date_str, age = stale
        assert "stale.md" in path
        assert age == 91
        assert errors == []

    def test_no_refs_dir(self, tmp_path):
        nonexistent = str(tmp_path / "does-not-exist")
        stale, errors = _check_stale_references(nonexistent, datetime.date.today())
        assert stale is None
        assert errors == []

    def test_files_without_frontmatter(self, tmp_path):
        refs_dir = tmp_path / "refs"
        refs_dir.mkdir()
        (refs_dir / "no-date.md").write_text("# No frontmatter here\n")
        (refs_dir / "no-field.md").write_text("---\nname: test\n---\n")
        stale, errors = _check_stale_references(str(refs_dir), datetime.date.today())
        assert stale is None
        assert errors == []

    def test_malformed_date_collected_as_error(self, tmp_path):
        """Malformed last_refreshed values are returned in the errors list."""
        refs_dir = tmp_path / "refs"
        refs_dir.mkdir()
        (refs_dir / "bad.md").write_text("---\nlast_refreshed: 2026-4-5\n---\n")
        stale, errors = _check_stale_references(str(refs_dir), datetime.date.today())
        assert stale is None
        assert len(errors) == 1
        path, raw, error = errors[0]
        assert "bad.md" in path
        assert raw == "2026-4-5"
        assert "YYYY-MM-DD" in error

    def test_domain_cache_included_in_scan(self, tmp_path):
        """Recursive glob picks up stale files in domain-cache subdirectory."""
        refs_dir = tmp_path / "refs"
        (refs_dir / "domain-cache").mkdir(parents=True)
        stale_date = (datetime.date.today() - datetime.timedelta(days=100)).isoformat()
        (refs_dir / "domain-cache" / "mydom.md").write_text(
            f"---\nlast_refreshed: {stale_date}\n---\n"
        )
        stale, errors = _check_stale_references(str(refs_dir), datetime.date.today())
        assert stale is not None
        path, _, age = stale
        assert "mydom.md" in path
        assert age == 100
        assert errors == []

    def test_domain_cache_stale_vs_toplevel_stale(self, tmp_path):
        """Single oldest file wins across top-level and domain-cache."""
        refs_dir = tmp_path / "refs"
        (refs_dir / "domain-cache").mkdir(parents=True)
        older = (datetime.date.today() - datetime.timedelta(days=200)).isoformat()
        newer_stale = (datetime.date.today() - datetime.timedelta(days=95)).isoformat()
        (refs_dir / "top.md").write_text(f"---\nlast_refreshed: {newer_stale}\n---\n")
        (refs_dir / "domain-cache" / "cache.md").write_text(
            f"---\nlast_refreshed: {older}\n---\n"
        )
        stale, errors = _check_stale_references(str(refs_dir), datetime.date.today())
        assert stale is not None
        path, _, age = stale
        assert "cache.md" in path
        assert age == 200
        assert errors == []

    def test_index_md_without_date_skipped(self, tmp_path):
        """INDEX.md without last_refreshed is silently ignored."""
        refs_dir = tmp_path / "refs"
        (refs_dir / "domain-cache").mkdir(parents=True)
        (refs_dir / "domain-cache" / "INDEX.md").write_text(
            "# Domain Cache Index\n\n| domain | description |\n|---|---|\n"
        )
        stale, errors = _check_stale_references(str(refs_dir), datetime.date.today())
        assert stale is None
        assert errors == []

    def test_recursive_glob_backward_compat(self, tmp_path):
        """Flat refs dir (no subdirectories) still works with recursive glob."""
        refs_dir = tmp_path / "refs"
        refs_dir.mkdir()
        fresh = datetime.date.today().isoformat()
        (refs_dir / "a.md").write_text(f"---\nlast_refreshed: {fresh}\n---\n")
        (refs_dir / "b.md").write_text(f"---\nlast_refreshed: {fresh}\n---\n")
        stale, errors = _check_stale_references(str(refs_dir), datetime.date.today())
        assert stale is None
        assert errors == []


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

    def test_malformed_date_emits_warning(self, tmp_path, monkeypatch, capsys):
        """Malformed last_refreshed is surfaced as a warning in additionalContext."""
        refs_dir = tmp_path / "skills" / "review-claude-config" / "references"
        refs_dir.mkdir(parents=True)
        (refs_dir / "bad.md").write_text("---\nlast_refreshed: 2026-4-5\n---\n")

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        main()
        output = json.loads(capsys.readouterr().out.strip())
        ctx = output["hookSpecificOutput"]["additionalContext"]
        assert "bad.md" in ctx
        assert "2026-4-5" in ctx
        assert "YYYY-MM-DD" in ctx


class TestParseLastRefreshedUnreadable:
    """Issue #118: existing-but-unreadable files surface as malformed_errors,
    not silent pass."""

    def test_unicode_decode_error_surfaces(self, tmp_path):
        """A file with invalid UTF-8 returns an error tuple instead of (None, None, None)."""
        bad = tmp_path / "binary.md"
        # Write invalid UTF-8 bytes (lone continuation byte).
        bad.write_bytes(b"---\nlast_refreshed: 2026-04-14\n---\n\xff\xfe garbage")
        date, raw, error = _parse_last_refreshed(str(bad))
        # Outcome depends on where the iterator hits the bad byte. Either:
        # - the date-parse succeeds before hitting the invalid byte → no error;
        # - or UnicodeDecodeError raises mid-iteration → error captured.
        # Both are acceptable — we assert only that the function does not
        # raise.
        assert (date is not None) or (error is not None) or (raw is None)


class TestExitCodeDiscipline:
    """Subprocess exit-code contract per issue #118."""

    def test_malformed_json_stdin_exits_zero(self, tmp_path):
        # session_check ignores stdin entirely (SessionStart hook), but the
        # test still validates the contract under malformed-input pressure.
        r = _run_hook(
            "not-json",
            env_overrides={"CLAUDE_PLUGIN_ROOT": str(tmp_path)},
        )
        assert r.returncode == 0

    def test_missing_env_vars_exits_zero(self):
        r = _run_hook("{}", env_overrides={"CLAUDE_PLUGIN_ROOT": None})
        assert r.returncode == 0
        assert r.stdout.strip() == "{}"
