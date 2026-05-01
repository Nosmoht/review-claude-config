"""Tests for hooks/session_audit.py — SessionEnd summary computation."""

import io
import json
import os
import pathlib
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from session_audit import _compute_summary, main

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "hooks" / "session_audit.py"


def _run(payload, env_overrides=None):
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


class TestComputeSummary:
    def test_basic_metrics(self):
        entries = [
            {"type": "tool_call", "ts": "2026-04-14T12:00:00+00:00", "success": True},
            {"type": "tool_call", "ts": "2026-04-14T12:01:00+00:00", "success": True},
            {"type": "tool_call", "ts": "2026-04-14T12:02:00+00:00", "success": False},
            {"type": "delegation", "ts": "2026-04-14T12:00:30+00:00", "event": "start"},
            {"type": "delegation", "ts": "2026-04-14T12:01:30+00:00", "event": "stop"},
        ]
        summary = _compute_summary(entries, "test-session")
        assert summary["type"] == "session_summary"
        assert summary["tool_calls"] == 3
        assert summary["tool_errors"] == 1
        assert summary["delegations"] == 1
        assert summary["max_depth"] == 1
        assert summary["duration_sec"] == 120

    def test_nested_delegation_depth(self):
        entries = [
            {"type": "delegation", "ts": "2026-04-14T12:00:00+00:00", "event": "start"},
            {"type": "delegation", "ts": "2026-04-14T12:00:10+00:00", "event": "start"},
            {"type": "delegation", "ts": "2026-04-14T12:00:20+00:00", "event": "start"},
            {"type": "delegation", "ts": "2026-04-14T12:00:30+00:00", "event": "stop"},
            {"type": "delegation", "ts": "2026-04-14T12:00:40+00:00", "event": "stop"},
            {"type": "delegation", "ts": "2026-04-14T12:00:50+00:00", "event": "stop"},
        ]
        summary = _compute_summary(entries, "test-session")
        assert summary["max_depth"] == 3
        assert summary["delegations"] == 3

    def test_empty_entries(self):
        summary = _compute_summary([], "test-session")
        assert summary["tool_calls"] == 0
        assert summary["duration_sec"] == 0

    def test_no_timestamps(self):
        entries = [
            {"type": "tool_call", "success": True},
        ]
        summary = _compute_summary(entries, "test-session")
        assert summary["duration_sec"] == 0


class TestMain:
    def test_no_plugin_data(self, monkeypatch, capsys):
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_no_audit_file(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps({"session_id": "nonexistent"})),
        )
        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_appends_summary(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        audit_file = audit_dir / "test-session.audit.jsonl"

        entries = [
            {"type": "tool_call", "ts": "2026-04-14T12:00:00+00:00", "success": True},
            {"type": "tool_call", "ts": "2026-04-14T12:05:00+00:00", "success": False},
        ]
        audit_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )

        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps({"session_id": "test-session"})),
        )
        main()

        lines = audit_file.read_text().strip().split("\n")
        assert len(lines) == 3  # 2 original + 1 summary
        summary = json.loads(lines[-1])
        assert summary["type"] == "session_summary"
        assert summary["tool_calls"] == 2
        assert summary["tool_errors"] == 1
        assert summary["duration_sec"] == 300

    def test_idempotent_no_duplicate_summary(self, monkeypatch, tmp_path):
        """Running SessionEnd twice does not append a second summary."""
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        audit_file = audit_dir / "test-session.audit.jsonl"

        entries = [
            {"type": "tool_call", "ts": "2026-04-14T12:00:00+00:00", "success": True},
        ]
        audit_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n"
        )

        # First run: appends summary
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps({"session_id": "test-session"})),
        )
        main()
        lines_after_first = audit_file.read_text().strip().split("\n")
        assert len(lines_after_first) == 2

        # Second run: idempotency guard prevents duplicate
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps({"session_id": "test-session"})),
        )
        main()
        lines_after_second = audit_file.read_text().strip().split("\n")
        assert len(lines_after_second) == 2  # unchanged

    def test_empty_audit_file(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        (audit_dir / "test-session.audit.jsonl").write_text("")

        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps({"session_id": "test-session"})),
        )
        main()
        assert capsys.readouterr().out.strip() == "{}"


class TestExitCodeDiscipline:
    """Subprocess exit-code contract per issue #118."""

    def test_malformed_json_stdin_exits_zero(self, tmp_path):
        r = _run("not-json", env_overrides={"CLAUDE_PLUGIN_DATA": str(tmp_path)})
        assert r.returncode == 0

    def test_missing_env_vars_exits_zero(self):
        r = _run("{}", env_overrides={"CLAUDE_PLUGIN_DATA": None})
        assert r.returncode == 0
        assert r.stdout.strip() == "{}"

    def test_audit_write_failure_exits_zero(self, tmp_path):
        # session_audit only writes when an audit file already exists;
        # set up a corrupt scenario: audit file is itself a directory, so
        # attempts to read/append raise OSError. Top-level wrapper must
        # catch and exit 0.
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        # Create a directory at the path where session_audit expects a file.
        bogus = audit_dir / "test-session.audit.jsonl"
        bogus.mkdir()
        payload = json.dumps({"session_id": "test-session"})
        r = _run(payload, env_overrides={"CLAUDE_PLUGIN_DATA": str(tmp_path)})
        assert r.returncode == 0
