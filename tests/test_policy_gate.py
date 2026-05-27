"""Tests for hooks/policy_gate.py — PreToolUse policy enforcement."""

import io
import json
import os
import pathlib
import sys

import jsonschema
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


def _evict_lazy_names() -> None:
    """Remove any lazy-load names that pytest's monkeypatch may have written
    into policy_gate.__dict__ as a side-effect of setattr-undo. Without this,
    a test that calls monkeypatch.setattr(policy_gate, 'TOOL_LEVELS', ...)
    and then monkeypatch.undo() leaves the real value in __dict__, bypassing
    __getattr__ for all subsequent tests in the same process."""
    import policy_gate

    for name in list(policy_gate._LAZY_NAMES):
        policy_gate.__dict__.pop(name, None)


@pytest.fixture(autouse=True)
def _isolate_policy_gate_state(monkeypatch):
    """Prevent test bleed across the whole module: clear lru_caches,
    evict lazy names from module __dict__, and unset POLICY_GATE_CONFIG_PATH
    around every test, regardless of pytest collection order or -n auto
    worker assignment.

    Mandatory because the existing 45 tests import lazy names via
    `from policy_gate import (DEFAULT_POLICY, ...)` at module load,
    populating the cache before any test runs. Without this fixture,
    a TestLazyLoadPolicy test that mutates POLICY_GATE_CONFIG_PATH
    would leak its synthetic config into a subsequent TestLoadPolicy
    or TestMain test on the same worker.
    """
    monkeypatch.delenv("POLICY_GATE_CONFIG_PATH", raising=False)
    import policy_gate
    policy_gate._load_config_cached.cache_clear()
    policy_gate._load_schema_cached.cache_clear()
    _evict_lazy_names()
    yield
    policy_gate._load_config_cached.cache_clear()
    policy_gate._load_schema_cached.cache_clear()
    _evict_lazy_names()


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

    Algorithm: an L1 shape (list_/get_/retrieve_/search_ prefix or _read
    suffix) is honored only when no token in the suffix is an L4 mutation
    verb. Token matching (split on '_') avoids substring collisions like
    'request' inside pull_request_read and lets compound idioms such as
    get_or_create_thing resolve to L4. Unknown shapes fall back to L4.
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

    def test_get_or_create_idiom_is_l4(self):
        # Real Django/REST idiom: get_or_create combines a read shape with a
        # mutation verb. Prefix-only matching would flip this to L1 (allow).
        assert _classify_mcp_tool("mcp__server__get_or_create_thing") == 4

    def test_list_and_delete_idiom_is_l4(self):
        # Compound name where the L4 verb appears inside the suffix.
        assert _classify_mcp_tool("mcp__server__list_and_delete_records") == 4

    def test_search_and_replace_idiom_is_l4(self):
        # 'replace' isn't an L4 verb, but 'update' is — covers the family of
        # destructive ops that hide behind a search_ prefix.
        assert _classify_mcp_tool("mcp__server__search_and_update") == 4

    def test_malformed_no_separator_is_l4(self):
        # Defensive: a tool name without the expected mcp__server__name shape
        # short-circuits to L4 instead of treating the whole string as suffix.
        assert _classify_mcp_tool("mcp_no_double_underscore") == 4

    def test_pull_request_read_is_l1(self):
        # Regression: 'request' was previously a verb in the L4 list and
        # substring matching flipped pull_request_read to L4 incorrectly.
        # Token-split classification keeps the noun 'request' distinct from
        # any mutation verb, and 'read' wins via the _read suffix.
        assert _classify_mcp_tool("mcp__github__pull_request_read") == 1

    def test_list_pull_requests_is_l1(self):
        # Regression: pluralized 'requests' as the suffix-tail must not flip
        # the read shape — the suffix 'list_pull_requests' has L1 shape and
        # contains no L4 verb token.
        assert _classify_mcp_tool("mcp__github__list_pull_requests") == 1

    def test_get_and_set_label_is_l4(self):
        # Round-2 verb extension: 'set' is a mutation verb and must override
        # the get_ prefix's L1 shape.
        assert _classify_mcp_tool("mcp__server__get_and_set_label") == 4

    def test_get_or_destroy_record_is_l4(self):
        # Round-2 verb extension: 'destroy' must override get_ L1 shape.
        assert _classify_mcp_tool("mcp__server__get_or_destroy_record") == 4

    def test_list_and_revoke_tokens_is_l4(self):
        # Round-2 verb extension: 'revoke' must override list_ L1 shape.
        assert _classify_mcp_tool("mcp__server__list_and_revoke_tokens") == 4


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


class TestAuditFailureIsolation:
    """Audit-log write failures must NEVER displace the deny/ask/allow JSON.

    Regression: prior to this fix, _log_decision raising (disk full,
    EACCES, broken mount) would bubble to the top-level except in
    __main__ and emit "{}" — which the harness reads as "no decision"
    and falls back to allow. A deny silently became an allow.

    The fix has two layers: (a) emit the JSON BEFORE calling
    _log_decision, and (b) _log_decision swallows OSError/TypeError/
    ValueError internally and writes to stderr.

    These tests cover the call-site contract by patching _log_decision
    to raise — exercising the belt-and-braces ordering guarantee — and
    also assert the stderr surface format.
    """

    @staticmethod
    def _raise_disk_full(*_args, **_kwargs):
        raise OSError("disk full")

    def test_deny_emitted_when_log_decision_raises(
        self, monkeypatch, tmp_path, capsys
    ):
        """L5 deny path: disk-full during audit must NOT downgrade to allow."""
        import policy_gate

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
        monkeypatch.setattr(policy_gate, "_log_decision", self._raise_disk_full)

        main()
        captured = capsys.readouterr()

        # Decision JSON must reach stdout, NOT "{}".
        output = json.loads(captured.out.strip())
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        # And the failure must surface on stderr in the contracted format.
        assert captured.err.startswith("Audit log write failed: ")
        assert "disk full" in captured.err

    def test_ask_emitted_when_log_decision_raises(
        self, monkeypatch, tmp_path, capsys
    ):
        """L4 ask path: disk-full during audit must NOT downgrade to allow."""
        import policy_gate

        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        policy_data = {
            "rules": [{"level": "L4", "action": "ask"}],
            "overrides": [],
        }
        (tmp_path / "policy.json").write_text(json.dumps(policy_data))

        input_data = {
            "session_id": "test",
            "tool_name": "Edit",
            "tool_input": {"file_path": "foo.py"},
        }
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        monkeypatch.setattr(policy_gate, "_log_decision", self._raise_disk_full)

        main()
        captured = capsys.readouterr()

        output = json.loads(captured.out.strip())
        assert output["hookSpecificOutput"]["permissionDecision"] == "ask"
        assert captured.err.startswith("Audit log write failed: ")
        assert "disk full" in captured.err

    def test_allow_path_still_emits_empty_when_log_decision_raises(
        self, monkeypatch, tmp_path, capsys
    ):
        """Allow path: _log_decision raises, hook must still emit "{}" — not
        an error JSON, not a deny/ask. The stderr message is still required."""
        import policy_gate

        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        policy_data = {
            "rules": [{"level": "L1", "action": "allow"}],
            "overrides": [],
        }
        (tmp_path / "policy.json").write_text(json.dumps(policy_data))

        input_data = {
            "session_id": "test",
            "tool_name": "Read",
            "tool_input": {"file_path": "/some/file"},
        }
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(input_data)))
        monkeypatch.setattr(policy_gate, "_log_decision", self._raise_disk_full)

        main()
        captured = capsys.readouterr()

        assert captured.out.strip() == "{}"
        assert captured.err.startswith("Audit log write failed: ")
        assert "disk full" in captured.err


class TestLogDecisionInternalIsolation:
    """The internal try/except in _log_decision itself must swallow disk
    errors and emit to stderr — independent of main()'s call-site ordering."""

    def test_oserror_in_makedirs_is_swallowed(
        self, monkeypatch, tmp_path, capsys
    ):
        import policy_gate

        def _boom(*_a, **_kw):
            raise OSError("EACCES on audit dir")

        monkeypatch.setattr(policy_gate.os, "makedirs", _boom)
        policy_gate._log_decision(
            str(tmp_path),
            {"session_id": "s", "tool_name": "Edit"},
            4,
            "ask",
        )
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err.startswith("Audit log write failed: ")
        assert "EACCES" in captured.err


class TestLazyLoadPolicy:
    """Cover the PEP 562 lazy-load path for the 5 JSON-derived constants."""

    def test_config_missing_raises_runtime_error(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ):
        """When policy_gate.json is missing, attribute access raises
        RuntimeError pointing at the config file."""
        import policy_gate

        monkeypatch.setenv("POLICY_GATE_CONFIG_PATH", str(tmp_path / "absent.json"))
        policy_gate._load_config_cached.cache_clear()
        try:
            with pytest.raises(
                RuntimeError,
                match=r"policy_gate\.json missing at .* — see hooks/policy_gate\.json",
            ):
                _ = policy_gate.TOOL_LEVELS
        finally:
            policy_gate._load_config_cached.cache_clear()

    def test_monkeypatch_setattr_is_reversible(self, monkeypatch: pytest.MonkeyPatch):
        """Pinned contract: setattr writes the name into __dict__ (short-
        circuiting __getattr__), monkeypatch.undo deletes it, and the next
        access re-resolves via the lazy-load path."""
        import policy_gate

        original_len = len(policy_gate.TOOL_LEVELS)
        monkeypatch.setattr(policy_gate, "TOOL_LEVELS", {"Fake": 1})
        assert policy_gate.TOOL_LEVELS == {"Fake": 1}
        monkeypatch.undo()
        assert len(policy_gate.TOOL_LEVELS) == original_len
        assert "Fake" not in policy_gate.TOOL_LEVELS

    def test_lazy_loaded_values_match_committed_json(self):
        """Sanity: lazy-loaded values match the JSON committed in the repo."""
        import policy_gate

        assert len(policy_gate.TOOL_LEVELS) == 12
        assert len(policy_gate.L5_BASH_PATTERNS) == 8
        assert len(policy_gate._MCP_L1_PREFIXES) == 4
        assert len(policy_gate._MCP_L4_VERBS) == 22
        assert len(policy_gate.DEFAULT_POLICY) == 5
        # Shape preservation
        assert isinstance(policy_gate.TOOL_LEVELS, dict)
        assert isinstance(policy_gate.L5_BASH_PATTERNS, list)
        assert isinstance(policy_gate._MCP_L1_PREFIXES, tuple)
        assert isinstance(policy_gate._MCP_L4_VERBS, frozenset)
        assert isinstance(policy_gate.DEFAULT_POLICY, dict)
        # DEFAULT_POLICY keys must be ints (coerced from JSON string keys)
        assert all(isinstance(k, int) for k in policy_gate.DEFAULT_POLICY)

    def test_env_var_overrides_default_path(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ):
        """env-var POLICY_GATE_CONFIG_PATH points to a synthetic config."""
        import policy_gate

        synthetic = {
            "policy_version": "1.0",
            "tool_levels": {"Custom": 1},
            "bash_l5_patterns": ["\\brm\\b"],
            "mcp_l1_prefixes": ["list_"],
            "mcp_l4_verbs": ["create"],
            "default_policy": {"1": "allow", "2": "allow", "3": "allow", "4": "ask", "5": "deny"},
        }
        config_file = tmp_path / "policy_gate.json"
        config_file.write_text(json.dumps(synthetic))
        monkeypatch.setenv("POLICY_GATE_CONFIG_PATH", str(config_file))
        policy_gate._load_config_cached.cache_clear()
        assert policy_gate.TOOL_LEVELS == {"Custom": 1}

    def test_malformed_json_raises_validation_error(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ):
        """A schema-mismatched JSON raises jsonschema.ValidationError on access."""
        import policy_gate

        bad_config = {"tool_levels": "not-a-dict"}
        config_file = tmp_path / "policy_gate.json"
        config_file.write_text(json.dumps(bad_config))
        monkeypatch.setenv("POLICY_GATE_CONFIG_PATH", str(config_file))
        policy_gate._load_config_cached.cache_clear()
        with pytest.raises((jsonschema.ValidationError, RuntimeError)):
            _ = policy_gate.TOOL_LEVELS
