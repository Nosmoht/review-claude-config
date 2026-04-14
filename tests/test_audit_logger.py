"""Tests for hooks/audit_logger.py — PostToolUse/PostToolUseFailure audit logging."""

import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from audit_logger import _hash_input, _audit_path, main


class TestHashInput:
    def test_deterministic(self):
        h1 = _hash_input({"command": "npm test"})
        h2 = _hash_input({"command": "npm test"})
        assert h1 == h2
        assert h1.startswith("sha256:")

    def test_different_inputs(self):
        h1 = _hash_input({"command": "npm test"})
        h2 = _hash_input({"command": "npm build"})
        assert h1 != h2

    def test_empty_input(self):
        h = _hash_input({})
        assert h.startswith("sha256:")

    def test_fallback_on_default_str(self):
        """json.dumps(obj, default=str) handles arbitrary objects — still produces a hash."""
        h = _hash_input(object())
        assert h.startswith("sha256:")
        assert h != "sha256:unknown"


class TestAuditPath:
    def test_creates_directory(self, tmp_path):
        path = _audit_path(str(tmp_path), "session-123")
        assert path.endswith("session-123.audit.jsonl")
        assert os.path.isdir(os.path.join(str(tmp_path), "audit"))


class TestMain:
    def test_no_plugin_data(self, monkeypatch, capsys):
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_writes_tool_call_entry(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        input_data = {
            "session_id": "test-session",
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_use_id": "toolu_01",
            "tool_input": {"command": "npm test"},
            "agent_id": None,
            "agent_type": None,
            "cwd": "/tmp",
        }
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        main()

        audit_file = tmp_path / "audit" / "test-session.audit.jsonl"
        assert audit_file.exists()
        entry = json.loads(audit_file.read_text().strip())
        assert entry["type"] == "tool_call"
        assert entry["tool_name"] == "Bash"
        assert entry["success"] is True
        assert entry["input_hash"].startswith("sha256:")

    def test_failure_event_sets_success_false(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        input_data = {
            "session_id": "test-session",
            "hook_event_name": "PostToolUseFailure",
            "tool_name": "Bash",
            "tool_use_id": "toolu_02",
            "tool_input": {"command": "failing-cmd"},
            "cwd": "/tmp",
        }
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        main()

        audit_file = tmp_path / "audit" / "test-session.audit.jsonl"
        entry = json.loads(audit_file.read_text().strip())
        assert entry["success"] is False

    def test_appends_multiple_entries(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        for i in range(3):
            input_data = {
                "session_id": "test-session",
                "hook_event_name": "PostToolUse",
                "tool_name": f"Tool{i}",
                "tool_use_id": f"toolu_{i}",
                "tool_input": {},
                "cwd": "/tmp",
            }
            monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
            main()

        audit_file = tmp_path / "audit" / "test-session.audit.jsonl"
        lines = audit_file.read_text().strip().split("\n")
        assert len(lines) == 3
