"""Tests for hooks/policy_gate.py — PreToolUse policy enforcement."""

import io
import json
import os
import pathlib
import sys

import jsonschema
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import policy_gate
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


class TestDecisionJsonFailClosedOnUnrecognizedAction:
    """#277 R1, R2 — _decision_json must NOT silently emit "{}" on unrecognized actions.

    Spec: issue #277 R1+R2 — four mis-action shapes covered (string typo, unknown
    verb, empty string, None). Per ai-written-tests.md practice #1, additional
    boundary cases (int, list, bool) cover the same defect class — JSON-parseable
    types that escape pure-string validation.
    """

    @pytest.mark.parametrize(
        "bad_action",
        [
            "Deny",   # capital-D typo
            "warn",   # unknown verb
            "",       # empty string
            None,     # null
            4,        # integer from policy.json {"action": 4}
            ["deny"], # list from policy.json {"action": ["deny"]}
            True,     # boolean from policy.json {"action": true}
            {"deny": True},  # dict
        ],
    )
    def test_unrecognized_action_emits_ask_json_not_empty_string(self, bad_action):
        """Spec #277 R1: result must be a JSON object with permissionDecision=ask,
        NOT the literal '{}' that the harness interprets as silent-allow."""
        result = policy_gate._decision_json(bad_action, 4, "Bash")
        assert result != "{}", (
            f"unrecognized action {bad_action!r} silently allowed via empty-JSON "
            f"emission — same defect class as issue #277"
        )
        parsed = json.loads(result)
        assert parsed["hookSpecificOutput"]["permissionDecision"] == "ask", (
            f"unrecognized action {bad_action!r} should fail-closed to ask, "
            f"not {parsed!r}"
        )
        # The unknown-verb reason must surface attacker-controlled bytes via
        # repr() so prompt-injection via stderr is mitigated.
        assert "unrecognized" in parsed["hookSpecificOutput"]["permissionDecisionReason"]


class TestLoadPolicyFailClosedOnResolveRaise:
    """#278 R1 — _load_policy must NOT raise out when _resolve raises.

    Spec: issue #278 R1+R3 — when _resolve('DEFAULT_POLICY') raises (canonical
    policy_gate.json missing, corrupted, or schema-invalid), _load_policy must
    return the hardcoded fail-closed dict instead of letting the raise reach
    __main__'s except-Exception → silent-allow path.
    """

    def test_when_canonical_policy_unreachable_returns_hardcoded_failclosed(
        self, tmp_path, monkeypatch, capsys
    ):
        """Spec #278 R1: monkeypatch _resolve to simulate canonical policy
        unreachable; _load_policy returns the hardcoded fail-closed dict and
        emits a warn to stderr; does NOT raise."""
        # Set up an empty policy.json (triggers the empty-policy fallback path)
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps({"rules": []}))

        def raising_resolve(name):
            raise RuntimeError(f"simulated canonical-policy corruption for {name!r}")

        monkeypatch.setattr(policy_gate, "_resolve", raising_resolve)

        result_policy, overrides = policy_gate._load_policy(str(tmp_path))

        # Fail-closed dict is the spec-defined posture, NOT the canonical default.
        # The literal values are checked against the documented contract (see
        # _HARDCODED_FAILCLOSED_POLICY definition + plan.md §Hardcoded fail-closed).
        assert result_policy == {1: "ask", 2: "ask", 3: "ask", 4: "deny", 5: "deny"}, (
            f"_load_policy on _resolve raise must return _HARDCODED_FAILCLOSED_POLICY, "
            f"got {result_policy!r}"
        )
        assert overrides == []
        captured = capsys.readouterr()
        assert "fail-closed" in captured.err
        assert "#278" in captured.err


class TestLoadPolicyValidatesActionsAtLoadTime:
    """#277 R3 — _load_policy validates action strings against {allow, ask, deny}
    at load time, on both rules[] and overrides[]. Substitutes 'ask' + stderr warn.
    """

    def test_unrecognized_rule_action_substituted_to_ask_with_stderr_warn(
        self, tmp_path, capsys
    ):
        """Spec #277 R3 — rules[]: unknown action verb substituted to ask."""
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps({"rules": [{"level": "L4", "action": "Deny"}]}))

        result_policy, _ = policy_gate._load_policy(str(tmp_path))

        assert result_policy[4] == "ask", (
            f"unknown rule action 'Deny' should be substituted to 'ask', got {result_policy[4]!r}"
        )
        captured = capsys.readouterr()
        assert "'Deny'" in captured.err
        assert "rule level=L4" in captured.err

    def test_unrecognized_override_action_substituted_to_ask(self, tmp_path, capsys):
        """Spec #277 R3 — overrides[]: unknown action verb substituted at load time.

        Closes the override-action-injection bypass that reviewer-flagged: a
        policy.json with overrides[].action='Allow' (capital A) or any non-canonical
        verb must NOT reach _decision_json with a fail-permissive value.
        """
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(
            json.dumps(
                {
                    "rules": [{"level": "L4", "action": "ask"}],
                    "overrides": [
                        {"tool": "Bash", "path_pattern": "*", "action": "Allow"}
                    ],
                }
            )
        )

        _, overrides = policy_gate._load_policy(str(tmp_path))

        assert overrides[0]["action"] == "ask", (
            f"override action 'Allow' should be substituted to 'ask' at load time, "
            f"got {overrides[0]['action']!r}"
        )
        captured = capsys.readouterr()
        assert "'Allow'" in captured.err
        assert "override tool=Bash" in captured.err


class TestMainEndToEndFailClosedOnMissingCanonical:
    """#278 R3 end-to-end — main() must NOT emit '{}' when canonical config missing.

    Spec: issue #278 R3 — hook stdout contract is non-{} JSON when _resolve
    raises. Phase 7.5 evaluator surfaced that the v3 fix only guarded
    _resolve('DEFAULT_POLICY') via _safe_resolve_default; _classify_tool's
    _resolve('TOOL_LEVELS') raise path bypassed it, propagated to __main__
    catch-all → '{}'. This test exercises main() end-to-end to lock in the
    follow-up fix (_safe_resolve helper used in _classify_tool / _classify_mcp_tool).
    """

    def test_when_canonical_policy_unreachable_main_emits_non_empty_decision(
        self, tmp_path, monkeypatch, capsys
    ):
        """Spec #278 R3: with canonical config missing AND user policy present,
        main() must emit a JSON object containing 'permissionDecision' on
        stdout, NOT the silent-allow '{}'."""
        # Point canonical config to a uniquely-named non-existent path
        missing_canonical = tmp_path / "no-such-policy-gate.json"
        monkeypatch.setenv("POLICY_GATE_CONFIG_PATH", str(missing_canonical))

        # Provide a user policy so _load_policy enters the load path (not None pass-through)
        plugin_data = tmp_path / "plugin"
        plugin_data.mkdir()
        (plugin_data / "audit").mkdir()
        (plugin_data / "policy.json").write_text(json.dumps({"rules": [], "overrides": []}))
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))

        # Clear LRU caches so the missing-canonical path is exercised this run
        policy_gate._load_config_cached.cache_clear()
        policy_gate._load_schema_cached.cache_clear()

        # Drive main() via stdin
        stdin_input = json.dumps(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "echo hi"},
                "session_id": "test",
            }
        )
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_input))

        policy_gate.main()

        captured = capsys.readouterr()
        assert captured.out.strip() != "{}", (
            f"main() must NOT emit silent-allow '{{}}' on missing canonical "
            f"config (Phase 7.5 evaluator finding for issue #278 R3); "
            f"got stdout={captured.out!r}"
        )
        # Parse the JSON; permissionDecision must be present
        parsed = json.loads(captured.out.strip())
        assert "hookSpecificOutput" in parsed, (
            f"main() stdout should be a hookSpecificOutput JSON, got {parsed!r}"
        )
        assert "permissionDecision" in parsed["hookSpecificOutput"], (
            f"missing permissionDecision in {parsed!r}"
        )
        # Under hardcoded fail-closed L4=deny, Bash is denied; under canonical L4=ask,
        # _safe_resolve fallback empty-dict-default gives L4 (since TOOL_LEVELS={}),
        # and _safe_resolve_default's hardcoded {4:"deny"} applies via policy.get.
        assert parsed["hookSpecificOutput"]["permissionDecision"] in ("ask", "deny"), (
            f"unexpected permissionDecision {parsed['hookSpecificOutput']['permissionDecision']!r}"
        )

        # Stderr should mention the fail-closed fallback for trace-ability
        assert "fail-closed" in captured.err
