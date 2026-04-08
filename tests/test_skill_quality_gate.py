"""Tests for hooks/skill_quality_gate.py — edit-time quality guideline injection."""

import json
import os
import textwrap

import pytest

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from skill_quality_gate import SKILL_PATTERNS, main


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

    def test_missing_guidelines_file(self, tmp_path, monkeypatch):
        # hooks/guidelines.md does not exist — main() raises FileNotFoundError
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        input_data = json.dumps({
            "tool_input": {"file_path": "/workspace/project/skills/my-skill/SKILL.md"}
        })
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(input_data))

        with pytest.raises(FileNotFoundError):
            main()

    def test_malformed_json_stdin(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path))
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO("not valid json{"))

        with pytest.raises(json.JSONDecodeError):
            main()
