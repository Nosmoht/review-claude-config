"""Tests for hooks/policy_gate.py — PreToolUse policy enforcement."""

import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from policy_gate import (
    DEFAULT_POLICY,
    _check_overrides,
    _classify_mcp_tool,
    _classify_tool,
    _load_policy,
    main,
)


class TestClassifyTool:
    def test_read_is_l1(self):
        assert _classify_tool("Read", {}) == 1

    def test_grep_is_l2(self):
        assert _classify_tool("Grep", {}) == 2

    def test_edit_is_l4(self):
        assert _classify_tool("Edit", {}) == 4

    def test_bash_default_is_l4(self):
        assert _classify_tool("Bash", {"command": "npm test"}) == 4

    def test_bash_rm_rf_escalates_to_l5(self):
        assert _classify_tool("Bash", {"command": "rm -rf /tmp/build"}) == 5

    def test_bash_force_push_escalates_to_l5(self):
        assert _classify_tool("Bash", {"command": "git push --force origin main"}) == 5

    def test_bash_reset_hard_escalates_to_l5(self):
        assert _classify_tool("Bash", {"command": "git reset --hard HEAD~3"}) == 5

    def test_unknown_tool_defaults_to_l4(self):
        assert _classify_tool("SomeNewTool", {}) == 4

    def test_mcp_create_is_l4(self):
        # Historic baseline test, kept for regression. New MCP coverage lives
        # in TestClassifyMCPTool below — this case exercises the create_ prefix
        # path through _classify_tool's MCP branch.
        assert _classify_tool("mcp__github__create_issue", {}) == 4

    def test_ask_user_is_l3(self):
        assert _classify_tool("AskUserQuestion", {}) == 3

    def test_bash_deploy_escalates_to_l5(self):
        assert _classify_tool("Bash", {"command": "deploy production"}) == 5


class TestClassifyMCPTool:
    """Pattern-based classification for mcp__* tool names.

    L1 reads: list_, get_, retrieve_, search_ prefixes + _read suffix.
    L4 mutations: create_/update_/delete_/archive_/unarchive_/add_/remove_/
    transfer_/assign_/merge_/push_/fork_/request_ prefixes + _write suffix.
    Unknown suffixes fall back to L4 conservatively.
    """

    def test_list_prefix_is_l1(self):
        assert _classify_mcp_tool("mcp__github__list_issues") == 1

    def test_retrieve_prefix_is_l1(self):
        assert _classify_mcp_tool("mcp__plane__retrieve_work_item") == 1

    def test_search_prefix_is_l1(self):
        assert _classify_mcp_tool("mcp__github__search_repositories") == 1

    def test_get_prefix_is_l1(self):
        assert _classify_mcp_tool("mcp__plane__get_me") == 1

    def test_read_suffix_is_l1(self):
        # GitHub MCP convention: issue_read / pull_request_read are reads.
        assert _classify_mcp_tool("mcp__github__issue_read") == 1

    def test_create_prefix_is_l4(self):
        assert _classify_mcp_tool("mcp__plane__create_work_item") == 4

    def test_delete_prefix_is_l4(self):
        assert _classify_mcp_tool("mcp__plane__delete_work_item") == 4

    def test_archive_prefix_is_l4(self):
        assert _classify_mcp_tool("mcp__plane__archive_cycle") == 4

    def test_add_prefix_is_l4(self):
        assert _classify_mcp_tool("mcp__plane__add_work_items_to_cycle") == 4

    def test_merge_prefix_is_l4(self):
        assert _classify_mcp_tool("mcp__github__merge_pull_request") == 4

    def test_write_suffix_is_l4(self):
        # GitHub MCP convention: issue_write / pull_request_review_write /
        # sub_issue_write are mutations dispatched via method= argument.
        assert _classify_mcp_tool("mcp__github__issue_write") == 4

    def test_unknown_suffix_defaults_to_l4(self):
        # Conservative fallback: any unrecognized verb stays at L4 (ask).
        assert _classify_mcp_tool("mcp__unknown__exotic_op") == 4


class TestLoadPolicy:
    def test_no_policy_file_returns_none(self, tmp_path):
        policy, overrides = _load_policy(str(tmp_path))
        assert policy is None
        assert overrides == []

    def test_valid_policy_file(self, tmp_path):
        policy_data = {
            "rules": [
                {"level": "L4", "action": "allow"},
                {"level": "L5", "action": "ask"},
            ],
            "overrides": [],
        }
        (tmp_path / "policy.json").write_text(json.dumps(policy_data))
        policy, overrides = _load_policy(str(tmp_path))
        assert policy[4] == "allow"
        assert policy[5] == "ask"

    def test_malformed_json_returns_default(self, tmp_path):
        """Malformed JSON triggers the except branch and falls back to
        DEFAULT_POLICY.

        Asserting against the imported DEFAULT_POLICY object (rather than the
        literal value) prevents a future widening of the default from making
        this test silently pass on the wrong code path.
        """
        (tmp_path / "policy.json").write_text("{ not valid json")
        policy, overrides = _load_policy(str(tmp_path))
        assert policy == DEFAULT_POLICY
        assert overrides == []

    def test_valid_rules_override_defaults(self, tmp_path):
        """Companion to test_malformed_json_returns_default: when JSON parses
        cleanly and contains rules, the *parsed* policy must surface
        non-default values. Together with the malformed-input test this
        triangulates that the except branch is the only code path that yields
        DEFAULT_POLICY on a present-but-broken file.
        """
        (tmp_path / "policy.json").write_text(
            '{"rules": [{"level": "L4", "action": "deny"}], "overrides": []}'
        )
        policy, overrides = _load_policy(str(tmp_path))
        # L4 action came from the file, NOT from DEFAULT_POLICY[4] which is "ask".
        assert policy[4] == "deny"
        assert policy != DEFAULT_POLICY


class TestCheckOverrides:
    def test_matching_override(self):
        overrides = [
            {"tool": "Write", "path_pattern": "reports/*", "action": "allow"}
        ]
        action = _check_overrides(
            overrides, "Write", {"file_path": "reports/report.md"}
        )
        assert action == "allow"

    def test_non_matching_override(self):
        overrides = [
            {"tool": "Write", "path_pattern": "reports/*", "action": "allow"}
        ]
        action = _check_overrides(
            overrides, "Write", {"file_path": "src/main.py"}
        )
        assert action is None

    def test_wrong_tool_no_match(self):
        overrides = [
            {"tool": "Write", "path_pattern": "*", "action": "allow"}
        ]
        action = _check_overrides(overrides, "Edit", {"file_path": "foo.py"})
        assert action is None


class TestMain:
    def test_no_plugin_data_passthrough(self, monkeypatch, capsys):
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_no_policy_file_passthrough(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        input_data = {
            "session_id": "test",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /"},
        }
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        main()
        # No policy.json → pass-through even for destructive commands
        assert capsys.readouterr().out.strip() == "{}"

    def test_policy_denies_l5(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        policy_data = {
            "rules": [{"level": "L5", "action": "deny"}],
            "overrides": [],
        }
        (tmp_path / "policy.json").write_text(json.dumps(policy_data))

        input_data = {
            "session_id": "test",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /tmp"},
        }
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        # Create audit dir so logging doesn't fail
        (tmp_path / "audit").mkdir()
        main()

        output = json.loads(capsys.readouterr().out.strip())
        decision = output["hookSpecificOutput"]["permissionDecision"]
        assert decision == "deny"

    def test_policy_allows_l1(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        policy_data = {
            "rules": [{"level": "L1", "action": "allow"}],
            "overrides": [],
        }
        (tmp_path / "policy.json").write_text(json.dumps(policy_data))
        (tmp_path / "audit").mkdir()

        input_data = {
            "session_id": "test",
            "tool_name": "Read",
            "tool_input": {"file_path": "/some/file"},
        }
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        main()
        assert capsys.readouterr().out.strip() == "{}"

    def test_override_bypasses_policy(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        policy_data = {
            "rules": [{"level": "L4", "action": "deny"}],
            "overrides": [
                {"tool": "Write", "path_pattern": "reports/*", "action": "allow"}
            ],
        }
        (tmp_path / "policy.json").write_text(json.dumps(policy_data))
        (tmp_path / "audit").mkdir()

        input_data = {
            "session_id": "test",
            "tool_name": "Write",
            "tool_input": {"file_path": "reports/report.md"},
        }
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        main()
        assert capsys.readouterr().out.strip() == "{}"  # allowed by override

    def test_logs_decision_to_audit(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        policy_data = {"rules": [{"level": "L4", "action": "ask"}], "overrides": []}
        (tmp_path / "policy.json").write_text(json.dumps(policy_data))

        input_data = {
            "session_id": "test-session",
            "tool_name": "Edit",
            "tool_input": {"file_path": "foo.py"},
        }
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        main()

        audit_file = tmp_path / "audit" / "test-session.audit.jsonl"
        assert audit_file.exists()
        entry = json.loads(audit_file.read_text().strip())
        assert entry["type"] == "policy_decision"
        assert entry["level"] == 4
        assert entry["action"] == "ask"
