"""Tests for hooks/skill_quality_gate.py — edit-time quality guideline injection."""

import json
import os
import pathlib
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from skill_quality_gate import SKILL_PATTERNS, main

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "hooks" / "skill_quality_gate.py"


class TestPatternMatching:
    """Verify SKILL_PATTERNS match the expected file types."""

    @pytest.mark.parametrize(
        "path",
        [
            "/home/user/project/skills/my-skill/SKILL.md",
            "/workspace/project/.claude/agents/reviewer.md",
            "/workspace/project/.claude/rules/safety.md",
        ],
    )
    def test_matching_paths(self, path):
        from fnmatch import fnmatch

        assert any(fnmatch(path, p) for p in SKILL_PATTERNS)

    @pytest.mark.parametrize(
        "path",
        [
            "/home/user/project/README.md",
            "/workspace/project/docs/guide.md",
            "/workspace/project/skills/my-skill/references/data.md",
            "/workspace/project/.claude/settings.json",
            "/workspace/project/CLAUDE.md",
        ],
    )
    def test_non_matching_paths(self, path):
        from fnmatch import fnmatch

        assert not any(fnmatch(path, p) for p in SKILL_PATTERNS)


class TestMain:
    def test_no_plugin_root(self, monkeypatch, capsys):
        monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("{}"))
        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_non_matching_file(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        input_data = json.dumps({"tool_input": {"file_path": "/some/project/README.md"}})
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(input_data))

        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_matching_skill_file(self, tmp_path, monkeypatch, capsys):
        # Create guidelines.md
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        guidelines = "## Quality Checklist\nCheck everything."
        (hooks_dir / "guidelines.md").write_text(guidelines)

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        input_data = json.dumps({
            "tool_input": {"file_path": "/workspace/project/skills/my-skill/SKILL.md"}
        })
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(input_data))

        main()
        output = json.loads(capsys.readouterr().out.strip())
        assert output["systemMessage"] == guidelines

    def test_matching_agent_file(self, tmp_path, monkeypatch, capsys):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        guidelines = "agent guidelines"
        (hooks_dir / "guidelines.md").write_text(guidelines)

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        input_data = json.dumps({
            "tool_input": {"file_path": "/project/.claude/agents/my-agent.md"}
        })
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(input_data))

        main()
        output = json.loads(capsys.readouterr().out.strip())
        assert output["systemMessage"] == guidelines

    def test_matching_rule_file(self, tmp_path, monkeypatch, capsys):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        guidelines = "rule guidelines"
        (hooks_dir / "guidelines.md").write_text(guidelines)

        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        input_data = json.dumps({
            "tool_input": {"file_path": "/project/.claude/rules/my-rule.md"}
        })
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(input_data))

        main()
        output = json.loads(capsys.readouterr().out.strip())
        assert output["systemMessage"] == guidelines

    def test_empty_file_path(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        input_data = json.dumps({"tool_input": {"file_path": ""}})
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(input_data))

        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_missing_file_path_key(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        input_data = json.dumps({"tool_input": {}})
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(input_data))

        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_missing_tool_input_key(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        input_data = json.dumps({"other": "data"})
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(input_data))

        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_missing_guidelines_file_passthrough(self, tmp_path):
        """A missing hooks/guidelines.md must NOT raise FileNotFoundError.

        The defensive `try/except OSError` around the `open()` call (issue
        #118) makes the hook degrade to a pass-through. We assert the
        end-to-end exit-code-zero contract via subprocess rather than
        in-process — `main()` no longer raises, so calling it directly would
        succeed silently and leak the stdout into capsys; the subprocess
        view is the contract Claude Code actually enforces.
        """
        env = os.environ.copy()
        env["CLAUDE_PLUGIN_ROOT"] = str(tmp_path)
        # Note: tmp_path/hooks/guidelines.md intentionally does not exist.
        payload = json.dumps({
            "tool_input": {"file_path": "/workspace/project/skills/my-skill/SKILL.md"}
        })
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
            check=False,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == "{}"


def _run(payload, env_overrides=None):
    """Invoke the hook via subprocess and return CompletedProcess."""
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


class TestExitCodeDiscipline:
    """Subprocess-level exit-code contract per issue #118.

    All hook scripts must `sys.exit(0)` on any exception (top-level wrapper)
    so Claude Code never blocks tool calls due to a hook crash. These tests
    enforce that contract for the three canonical failure inputs.
    """

    def test_malformed_json_stdin_exits_zero(self, tmp_path):
        r = _run(
            "not-json",
            env_overrides={"CLAUDE_PLUGIN_ROOT": str(tmp_path)},
        )
        assert r.returncode == 0

    def test_missing_env_vars_exits_zero(self, tmp_path):
        # CLAUDE_PLUGIN_ROOT absent → early-return pass-through
        r = _run(
            "{}",
            env_overrides={"CLAUDE_PLUGIN_ROOT": None},
        )
        assert r.returncode == 0
        # Early exit prints "{}" — verify pass-through stays clean.
        assert r.stdout.strip() == "{}"
