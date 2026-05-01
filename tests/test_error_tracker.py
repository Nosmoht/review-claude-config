"""Tests for hooks/error_tracker.py — StopFailure API error logging."""

import io
import json
import os
import pathlib
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from error_tracker import main

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "hooks" / "error_tracker.py"


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
        not_a_dir = tmp_path / "not-a-dir"
        not_a_dir.write_text("blocked")
        payload = json.dumps({
            "session_id": "s1",
            "hook_event_name": "StopFailure",
            "error_type": "rate_limit",
        })
        r = _run(payload, env_overrides={"CLAUDE_PLUGIN_DATA": str(not_a_dir)})
        assert r.returncode == 0
