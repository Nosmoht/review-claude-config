"""Tests for hooks/audit_rotator.py."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "hooks" / "audit_rotator.py"


def _run(plugin_data: pathlib.Path, session_id: str = "s1") -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_DATA"] = str(plugin_data)
    payload = json.dumps({"session_id": session_id})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
        check=False,
    )


class TestRotator:
    def test_no_rotation_small_file(self, tmp_path: pathlib.Path):
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        src = audit_dir / "s1.audit.jsonl"
        src.write_text('{"x": 1}\n')
        r = _run(tmp_path)
        assert r.returncode == 0
        assert src.exists()
        assert not (audit_dir / "s1.audit.jsonl.1").exists()

    def test_rotation_over_threshold(self, tmp_path: pathlib.Path):
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        src = audit_dir / "s1.audit.jsonl"
        # Write >10 MB
        big = "x" * (10 * 1024 * 1024 + 1024)
        src.write_text(big)
        r = _run(tmp_path)
        assert r.returncode == 0
        assert not src.exists()
        assert (audit_dir / "s1.audit.jsonl.1").exists()

    def test_three_generation_drop(self, tmp_path: pathlib.Path):
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        (audit_dir / "s1.audit.jsonl.2").write_text("older")
        (audit_dir / "s1.audit.jsonl.1").write_text("old")
        src = audit_dir / "s1.audit.jsonl"
        big = "x" * (10 * 1024 * 1024 + 1024)
        src.write_text(big)
        r = _run(tmp_path)
        assert r.returncode == 0
        # .2 was dropped (replaced), .1 promoted, src moved to .1 (clobbering)
        # Expected: src gone, .1 present (was src), .2 present? Actually the
        # rotator drops .2 then promotes .1→.2 then src→.1. So:
        assert not src.exists()
        # .1 is now the new src content
        assert (audit_dir / "s1.audit.jsonl.1").exists()

    def test_no_plugin_data_no_op(self):
        env = os.environ.copy()
        env.pop("CLAUDE_PLUGIN_DATA", None)
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input='{"session_id": "x"}',
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
            check=False,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == "{}"

    def test_missing_audit_file_no_op(self, tmp_path: pathlib.Path):
        r = _run(tmp_path, session_id="nonexistent")
        assert r.returncode == 0
        assert r.stdout.strip() == "{}"

    def test_invalid_json_input_no_crash(self, tmp_path: pathlib.Path):
        env = os.environ.copy()
        env["CLAUDE_PLUGIN_DATA"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not-json",
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
            check=False,
        )
        assert r.returncode == 0
