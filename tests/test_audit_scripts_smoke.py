"""Smoke tests for audit/utility scripts that the existing integration tests
invoke as subprocesses (and therefore miss coverage credit on).

These tests import each module in-process and call its ``main()`` so coverage
records the executed lines. They are deliberately lightweight — the deeper
behavior is covered by the existing subprocess-based tests."""

from __future__ import annotations

import io
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
HOOKS_DIR = REPO_ROOT / "hooks"

# Allow ``import audit_suite`` etc. without packaging the scripts dir.
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(HOOKS_DIR))


class TestAuditSuiteMain:
    def test_main_succeeds(self, capsys):
        import audit_suite

        rc = audit_suite.main(show_fail_paths=False)
        out = capsys.readouterr().out
        assert rc == 0
        assert "# Suite Audit" in out
        assert "## Aggregate Verdict Counts" in out

    def test_main_with_fail_paths(self, capsys):
        import audit_suite

        rc = audit_suite.main(show_fail_paths=True)
        out = capsys.readouterr().out
        assert rc == 0
        assert "Total FAIL count" in out


class TestAuditDescriptionCollisionMain:
    def test_main_default_threshold(self, capsys):
        import audit_description_collision

        rc = audit_description_collision.main(threshold=0.3)
        out = capsys.readouterr().out
        assert rc == 0
        assert "Description-Collision Audit" in out
        assert "Counter-Reference Regex Coverage" in out

    def test_jaccard_helper(self):
        import audit_description_collision

        assert audit_description_collision.jaccard(set(), set()) == 0.0
        assert audit_description_collision.jaccard({"a", "b"}, {"a", "b"}) == 1.0
        assert audit_description_collision.jaccard({"a"}, {"b"}) == 0.0


class TestAuditPreflightMain:
    def test_main_no_paths(self, capsys):
        import audit_preflight

        rc = audit_preflight.main(show_paths=False)
        out = capsys.readouterr().out
        assert rc == 0
        # Output lists per-item counts; at least one item ID is mentioned.
        assert any(item in out for item in ("WS-7", "WS-8", "GA-Y", "CE-CP"))

    def test_main_with_paths(self, capsys):
        import audit_preflight

        rc = audit_preflight.main(show_paths=True)
        out = capsys.readouterr().out
        assert rc == 0


class TestAuditRotatorInProcess:
    def test_rotate_no_plugin_data_emits_empty_object(self, monkeypatch, capsys):
        import audit_rotator

        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        monkeypatch.setattr(sys, "stdin", io.StringIO('{"session_id": "s1"}'))
        audit_rotator.main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_rotate_invalid_json_emits_empty_object(self, monkeypatch, tmp_path, capsys):
        import audit_rotator

        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        monkeypatch.setattr(sys, "stdin", io.StringIO("{not valid json"))
        audit_rotator.main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_rotate_missing_session_id_emits_empty_object(self, monkeypatch, tmp_path, capsys):
        import audit_rotator

        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))
        audit_rotator.main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_rotate_missing_audit_file_emits_empty_object(self, monkeypatch, tmp_path, capsys):
        import audit_rotator

        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        monkeypatch.setattr(sys, "stdin", io.StringIO('{"session_id": "missing"}'))
        audit_rotator.main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_rotate_small_file_no_op(self, monkeypatch, tmp_path, capsys):
        import audit_rotator

        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        audit_path = audit_dir / "s1.audit.jsonl"
        audit_path.write_text("{}\n")
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        monkeypatch.setattr(sys, "stdin", io.StringIO('{"session_id": "s1"}'))
        audit_rotator.main()
        assert capsys.readouterr().out.strip() == "{}"
        assert audit_path.exists()

    def test_rotate_large_file_rotates(self, monkeypatch, tmp_path, capsys):
        import audit_rotator

        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        audit_path = audit_dir / "s1.audit.jsonl"
        # Write just over the 10 MB threshold.
        audit_path.write_bytes(b"x" * (audit_rotator.ROTATE_THRESHOLD_BYTES + 1))
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        monkeypatch.setattr(sys, "stdin", io.StringIO('{"session_id": "s1"}'))
        audit_rotator.main()
        assert capsys.readouterr().out.strip() == "{}"
        assert (audit_dir / "s1.audit.jsonl.1").exists()
        assert not audit_path.exists()

    def test_rotate_drops_oldest_generation(self, tmp_path):
        import audit_rotator

        base = tmp_path / "x.jsonl"
        base.write_text("live")
        (tmp_path / "x.jsonl.1").write_text("gen1")
        (tmp_path / "x.jsonl.2").write_text("gen2")
        audit_rotator._rotate(str(base))
        # MAX_GENERATIONS=2 means slots .1 and .2 are kept; .2 is dropped first,
        # then .1 → .2, then live → .1.
        assert (tmp_path / "x.jsonl.1").read_text() == "live"
        assert (tmp_path / "x.jsonl.2").read_text() == "gen1"
        assert not base.exists()
