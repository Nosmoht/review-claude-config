"""Tests for hooks/error_tracker.py — StopFailure API error logging."""

import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from error_tracker import main


class TestMain:
    def test_no_plugin_data(self, monkeypatch, capsys):
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_writes_api_error_entry(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        input_data = {
            "session_id": "test-session",
            "hook_event_name": "StopFailure",
            "error_type": "rate_limit",
            "agent_id": None,
            "cwd": "/tmp",
        }
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        main()

        audit_file = tmp_path / "audit" / "test-session.audit.jsonl"
        assert audit_file.exists()
        entry = json.loads(audit_file.read_text().strip())
        assert entry["type"] == "api_error"
        assert entry["error_type"] == "rate_limit"

    def test_unknown_error_type(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        input_data = {"session_id": "test-session"}
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        main()

        audit_file = tmp_path / "audit" / "test-session.audit.jsonl"
        entry = json.loads(audit_file.read_text().strip())
        assert entry["error_type"] == "unknown"

    def test_appends_to_existing_log(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        for error in ["rate_limit", "server_error"]:
            input_data = {
                "session_id": "test-session",
                "error_type": error,
            }
            monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
            main()

        audit_file = tmp_path / "audit" / "test-session.audit.jsonl"
        lines = audit_file.read_text().strip().split("\n")
        assert len(lines) == 2
