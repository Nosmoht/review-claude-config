"""Tests for hooks/session_audit.py — SessionEnd summary computation."""

import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from session_audit import _compute_summary, main


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
