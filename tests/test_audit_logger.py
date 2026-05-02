"""Tests for hooks/audit_logger.py — PostToolUse/PostToolUseFailure audit logging."""

import io
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from audit_logger import _hash_input, _audit_path, main

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "hooks" / "audit_logger.py"


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


class TestExitCodeDiscipline:
    """Subprocess exit-code contract per issue #118."""

    def test_malformed_json_stdin_exits_zero(self, tmp_path):
        r = _run(
            "not-json",
            env_overrides={"CLAUDE_PLUGIN_DATA": str(tmp_path)},
        )
        assert r.returncode == 0

    def test_missing_env_vars_exits_zero(self):
        r = _run("{}", env_overrides={"CLAUDE_PLUGIN_DATA": None})
        assert r.returncode == 0
        assert r.stdout.strip() == "{}"

    def test_audit_write_failure_exits_zero(self, tmp_path):
        # Point CLAUDE_PLUGIN_DATA at an existing regular file rather than a
        # directory. os.makedirs(plugin_data + "/audit", exist_ok=True) then
        # raises NotADirectoryError (an OSError subclass) — the top-level
        # wrapper must catch it and exit 0.
        not_a_dir = tmp_path / "not-a-dir"
        not_a_dir.write_text("blocked")
        payload = json.dumps({
            "session_id": "s1",
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "x"},
            "cwd": "/tmp",
        })
        r = _run(payload, env_overrides={"CLAUDE_PLUGIN_DATA": str(not_a_dir)})
        assert r.returncode == 0
        # Pin the stdout contract too: the TL wrapper prints "{}" so a hook
        # that exits 0 but emits hook-output garbage on the failure path
        # would not silently pass.
        assert r.stdout.strip() == "{}"


class TestRedaction:
    """$HOME redaction contract for the cwd field per docs/hook-governance.md.

    All tests use the _run() subprocess pattern with env_overrides so that
    _HOME and _REDACT_ENABLED are resolved at module-load time inside the
    subprocess — exactly as in production. No importlib.reload is used.
    """

    def test_redaction_cwd_home_prefix(self, tmp_path):
        """cwd starting with $HOME is replaced with '~'; other fields unchanged."""
        fake_home = str(tmp_path / "fakehome")
        cwd_value = fake_home + "/foo/bar"
        payload = json.dumps({
            "session_id": "r-session",
            "hook_event_name": "PostToolUse",
            "tool_name": "Read",
            "tool_use_id": "toolu_r1",
            "tool_input": {"file_path": "/tmp/x"},
            "cwd": cwd_value,
        })
        r = _run(
            payload,
            env_overrides={
                "CLAUDE_PLUGIN_DATA": str(tmp_path),
                "HOME": fake_home,
            },
        )
        assert r.returncode == 0
        audit_file = tmp_path / "audit" / "r-session.audit.jsonl"
        assert audit_file.exists(), "audit file not written"
        entry = json.loads(audit_file.read_text().strip())
        assert entry["cwd"] == "~/foo/bar", f"expected ~/foo/bar, got {entry['cwd']!r}"
        # Scoping check: unrelated fields must be untouched
        assert entry["tool_name"] == "Read"
        assert entry["success"] is True

    def test_redaction_cwd_no_home_prefix_unchanged(self, tmp_path):
        """cwd not under $HOME is written verbatim."""
        fake_home = str(tmp_path / "fakehome")
        payload = json.dumps({
            "session_id": "r-session2",
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_use_id": "toolu_r2",
            "tool_input": {},
            "cwd": "/tmp/xyz",
        })
        r = _run(
            payload,
            env_overrides={
                "CLAUDE_PLUGIN_DATA": str(tmp_path),
                "HOME": fake_home,
            },
        )
        assert r.returncode == 0
        audit_file = tmp_path / "audit" / "r-session2.audit.jsonl"
        entry = json.loads(audit_file.read_text().strip())
        assert entry["cwd"] == "/tmp/xyz", f"expected /tmp/xyz, got {entry['cwd']!r}"

    def test_redaction_cwd_none_passthrough(self, tmp_path):
        """Omitting cwd key results in cwd=None in audit entry; no error."""
        fake_home = str(tmp_path / "fakehome")
        payload = json.dumps({
            "session_id": "r-session3",
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_use_id": "toolu_r3",
            "tool_input": {},
            # cwd key intentionally absent
        })
        r = _run(
            payload,
            env_overrides={
                "CLAUDE_PLUGIN_DATA": str(tmp_path),
                "HOME": fake_home,
            },
        )
        assert r.returncode == 0
        audit_file = tmp_path / "audit" / "r-session3.audit.jsonl"
        entry = json.loads(audit_file.read_text().strip())
        assert entry["cwd"] is None, f"expected None, got {entry['cwd']!r}"

    def test_redaction_empty_home_env_disables(self, tmp_path):
        """Empty HOME disables redaction; cwd is written verbatim."""
        payload = json.dumps({
            "session_id": "r-session4",
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_use_id": "toolu_r4",
            "tool_input": {},
            "cwd": "/tmp/foo",
        })
        r = _run(
            payload,
            env_overrides={
                "CLAUDE_PLUGIN_DATA": str(tmp_path),
                "HOME": "",
            },
        )
        assert r.returncode == 0
        audit_file = tmp_path / "audit" / "r-session4.audit.jsonl"
        entry = json.loads(audit_file.read_text().strip())
        # Empty HOME → _REDACT_ENABLED = False → no ~ substitution
        assert entry["cwd"] == "/tmp/foo", f"expected /tmp/foo, got {entry['cwd']!r}"

    def test_redaction_home_prefix_collision_safe(self, tmp_path):
        """cwd sharing a byte-prefix but NOT a path-component boundary is unchanged."""
        fake_home = str(tmp_path / "home")
        # fake_home = <tmp_path>/home ; cwd = <tmp_path>/homer/x
        # "homer" starts with "home" but is NOT under "home/" (different dir)
        homer_dir = str(tmp_path / "homer" / "x")
        payload = json.dumps({
            "session_id": "r-session5",
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_use_id": "toolu_r5",
            "tool_input": {},
            "cwd": homer_dir,
        })
        r = _run(
            payload,
            env_overrides={
                "CLAUDE_PLUGIN_DATA": str(tmp_path),
                "HOME": fake_home,
            },
        )
        assert r.returncode == 0
        audit_file = tmp_path / "audit" / "r-session5.audit.jsonl"
        entry = json.loads(audit_file.read_text().strip())
        # Should NOT be replaced — boundary check prevents collision
        assert entry["cwd"] == homer_dir, (
            f"boundary check failed: expected {homer_dir!r}, got {entry['cwd']!r}"
        )
