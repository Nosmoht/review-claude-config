#!/usr/bin/env python3
"""PreToolUse hook: classify tool calls by action level and enforce policy.

Hook type: PreToolUse
Trigger: (all tools — no matcher, so every tool call is evaluated)
Output: permissionDecision (allow/ask/deny) based on action classification

Reads policy from $CLAUDE_PLUGIN_DATA/policy.json if available.
Falls back to default policy: L1-L3 allow, L4 ask, L5 deny.
Also logs the policy decision to the audit trace.
"""

from __future__ import annotations

import datetime
import functools
import json
import os
import pathlib
import re
import sys
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Declared for static analysis (ruff F821, mypy/pyright). Resolved at
    # runtime via PEP 562 __getattr__ from policy_gate.json.
    TOOL_LEVELS: dict[str, int]
    L5_BASH_PATTERNS: list[str]
    DEFAULT_POLICY: dict[int, str]
    _MCP_L1_PREFIXES: tuple[str, ...]
    _MCP_L4_VERBS: frozenset[str]

LEVEL_LABELS = {1: "Read", 2: "Analyze", 3: "Recommend", 4: "Act", 5: "Irreversible"}

# Defense-in-depth fail-closed posture for #278.
# Used ONLY when _resolve("DEFAULT_POLICY") raises (canonical policy_gate.json
# unreachable or corrupted). Intentionally stricter than canonical default_policy
# (which is L1-L3 allow, L4 ask, L5 deny) to make sessions degrade conservatively.
# DO NOT refactor into _resolve(...) call: the duplication IS the defense — if
# the canonical source is unreachable, this hardcoded copy MUST remain reachable
# in-process. See issue #278 and plan.md §Hardcoded fail-closed default.
# MappingProxyType wraps a plain dict to make module-level state read-only,
# defending against in-process mutation by sibling tests or compromised callers
# (per v2 reviewer team-red H_T2). Callers MUST defensively `dict(...)` to copy
# before returning since downstream code may need a mutable dict.
_HARDCODED_FAILCLOSED_POLICY = MappingProxyType({1: "ask", 2: "ask", 3: "ask", 4: "deny", 5: "deny"})

_VALID_ACTIONS = frozenset({"allow", "ask", "deny"})

_LAZY_NAMES = frozenset(
    {
        "TOOL_LEVELS",
        "L5_BASH_PATTERNS",
        "DEFAULT_POLICY",
        "_MCP_L1_PREFIXES",
        "_MCP_L4_VERBS",
    }
)

# Test injection: POLICY_GATE_CONFIG_PATH overrides the default; otherwise
# resolve relative to the file (mirrors YAML_PATH idiom in merge_findings.py).
_DEFAULT_CONFIG_PATH = pathlib.Path(__file__).resolve().parent / "policy_gate.json"


def _config_path() -> pathlib.Path:
    override = os.environ.get("POLICY_GATE_CONFIG_PATH")
    return pathlib.Path(override) if override else _DEFAULT_CONFIG_PATH


_SCHEMA_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "skills/review-claude-config/references/schemas/policy_gate.schema.json"
)

# Inline shape-check used as graceful-degradation fallback when the
# canonical schema file is missing (e.g., directory reorg) — defends the
# env-var injection seam at minimal-shape level even without the full
# schema. Prevents the team-red R2 ScenarioB failure mode (silent hook
# disablement on schema relocation).
_REQUIRED_KEYS = (
    "policy_version",
    "tool_levels",
    "bash_l5_patterns",
    "mcp_l1_prefixes",
    "mcp_l4_verbs",
    "default_policy",
)


def _minimal_shape_check(data: Any) -> None:
    if not isinstance(data, dict):
        raise RuntimeError("policy_gate.json: top-level must be object")
    missing = [k for k in _REQUIRED_KEYS if k not in data]
    if missing:
        raise RuntimeError(f"policy_gate.json: missing required keys {missing}")
    if not isinstance(data["tool_levels"], dict):
        raise RuntimeError("policy_gate.json: tool_levels must be object")
    if not isinstance(data["default_policy"], dict):
        raise RuntimeError("policy_gate.json: default_policy must be object")
    for arr_key in ("bash_l5_patterns", "mcp_l1_prefixes", "mcp_l4_verbs"):
        if not isinstance(data[arr_key], list):
            raise RuntimeError(f"policy_gate.json: {arr_key} must be array")


@functools.lru_cache(maxsize=1)
def _load_schema_cached() -> dict[str, Any] | None:
    """Load the JSON Schema. Return None if the canonical schema file
    has been relocated or removed — caller falls back to inline shape
    check. Mirrors merge_findings.py's tolerance of yaml-missing failure mode."""
    try:
        with _SCHEMA_PATH.open(encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return None


@functools.lru_cache(maxsize=1)
def _load_config_cached(path: str) -> dict[str, Any]:
    """Load + validate policy_gate.json.

    Validation strategy (defense in depth):
    1. If the canonical schema is reachable, run full
       jsonschema.Draft202012Validator(schema).validate(data).
    2. Else fall back to an inline _minimal_shape_check(data) that
       enforces top-level keys + nested-container types. Both paths
       defend the env-var injection seam (AC #5) by rejecting
       runtime-supplied JSONs whose shape doesn't match policy_gate.json.
    """
    p = pathlib.Path(path)
    if not p.exists():
        raise RuntimeError(f"policy_gate.json missing at {p} — see hooks/policy_gate.json")
    with p.open(encoding="utf-8") as fh:
        data = json.load(fh)
    schema = _load_schema_cached()
    if schema is not None:
        import jsonschema  # local import on cache-miss only

        jsonschema.Draft202012Validator(schema).validate(data)
    else:
        _minimal_shape_check(data)
    return data


def _load_config() -> dict[str, Any]:
    return _load_config_cached(str(_config_path()))


def _resolve(name: str) -> Any:
    cfg = _load_config()
    if name == "TOOL_LEVELS":
        return dict(cfg["tool_levels"])
    if name == "L5_BASH_PATTERNS":
        return list(cfg["bash_l5_patterns"])
    if name == "DEFAULT_POLICY":
        return {int(k): v for k, v in cfg["default_policy"].items()}
    if name == "_MCP_L1_PREFIXES":
        return tuple(cfg["mcp_l1_prefixes"])
    if name == "_MCP_L4_VERBS":
        return frozenset(cfg["mcp_l4_verbs"])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __getattr__(name: str) -> Any:  # PEP 562
    if name in _LAZY_NAMES:
        return _resolve(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _classify_mcp_tool(tool_name):
    """Classify an mcp__ tool by name pattern. Default L4 for unknown suffixes."""
    if "__" not in tool_name:
        return 4  # malformed name — conservative fallback
    suffix = tool_name.split("__")[-1]
    is_l1_shape = any(suffix.startswith(p) for p in _resolve("_MCP_L1_PREFIXES")) or suffix.endswith("_read")
    has_l4_verb = bool(set(suffix.split("_")) & _resolve("_MCP_L4_VERBS"))
    if is_l1_shape and not has_l4_verb:
        return 1
    return 4


def _classify_tool(tool_name, tool_input):
    """Return authorization level (1-5) for a tool call."""
    level = _resolve("TOOL_LEVELS").get(tool_name, 4)  # unknown tools default to L4

    # MCP tools: pattern-based classification (reads vs mutations vs unknown)
    if tool_name.startswith("mcp__"):
        level = _classify_mcp_tool(tool_name)

    # Bash escalation check
    if tool_name == "Bash" and level == 4:
        command = tool_input.get("command", "")
        for pattern in _resolve("L5_BASH_PATTERNS"):
            if re.search(pattern, command, re.IGNORECASE):
                return 5

    return level


def _validated_action(raw_action, where, default="ask"):
    """Return raw_action if it's a recognized action verb, else default + stderr warn.

    Called from both policy-rule loading and override-rule loading so the
    fail-closed default reaches every action-string parse site at load time.

    `where` is repr-escaped before formatting to prevent attacker-controlled
    policy.json byte injection into stderr (which the harness captures into
    the orchestrator context per rules/tool-error-contract.md). v2 reviewer
    team-red H_T3.
    """
    if isinstance(raw_action, str) and raw_action in _VALID_ACTIONS:
        return raw_action
    sys.stderr.write(
        f"policy_gate: unrecognized action {raw_action!r} at {where!r}; substituting {default!r} (fail-closed)\n"
    )
    return default


def _safe_resolve_default():
    """Return canonical DEFAULT_POLICY, OR hardcoded fail-closed dict on any raise.

    Catches the documented raise classes from _resolve → _load_config_cached:
    RuntimeError (from _minimal_shape_check + 'policy_gate.json missing'),
    jsonschema.exceptions.ValidationError (schema-invalid canonical),
    FileNotFoundError, json.JSONDecodeError. Imports jsonschema lazily inside
    the function to preserve graceful-degradation when jsonschema is not
    importable (matches the conditional-import pattern in _load_config_cached).
    Final `except Exception` is the defense-in-depth catch-all for unforeseen
    raise classes; KeyboardInterrupt / SystemExit / MemoryError still propagate
    via Python's BaseException hierarchy.
    """
    # Lazy-imported tuple — match _load_config_cached's pattern.
    failure_types = [RuntimeError, FileNotFoundError, json.JSONDecodeError]
    try:
        import jsonschema  # may itself raise ImportError

        failure_types.append(jsonschema.exceptions.ValidationError)
    except ImportError:
        pass  # ValidationError won't be raised if jsonschema is unimportable

    try:
        return _resolve("DEFAULT_POLICY")
    except tuple(failure_types) as e:
        sys.stderr.write(
            f"policy_gate: _resolve(DEFAULT_POLICY) raised {type(e).__name__}: {e!s}; "
            f"falling back to hardcoded fail-closed posture (#278)\n"
        )
        return dict(_HARDCODED_FAILCLOSED_POLICY)
    except Exception as e:  # noqa: BLE001 — defense-in-depth catch-all
        sys.stderr.write(
            f"policy_gate: _resolve(DEFAULT_POLICY) raised unforeseen {type(e).__name__}: {e!s}; "
            f"falling back to hardcoded fail-closed posture (#278)\n"
        )
        return dict(_HARDCODED_FAILCLOSED_POLICY)


def _load_policy(plugin_data):
    """Load policy from file. Return None if no policy file exists (opt-in design).

    Both action-string parsing and the canonical-default fallback use
    fail-closed semantics: unrecognized action verbs are substituted with
    "ask" + stderr warn (#277 R3); _resolve raises yield a hardcoded
    fail-closed dict (#278 R1). OSError (PermissionError on policy.json,
    stale-mount, etc.) is added to the except tuple to close the parallel
    fall-open path on the user policy.json file (v2 reviewer M_R1).
    """
    policy_path = os.path.join(plugin_data, "policy.json")
    if not os.path.isfile(policy_path):
        return None, []  # No policy file = pass-through, zero enforcement
    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        policy = {}
        for rule in data.get("rules", []):
            level_str = rule.get("level", "")
            if level_str.startswith("L") and level_str[1:].isdigit():
                raw_action = rule.get("action", "ask")
                policy[int(level_str[1:])] = _validated_action(raw_action, f"rule level={level_str}")
        # Validate override actions at load time too — same defect class as rules.
        overrides = data.get("overrides", [])
        for override in overrides:
            if "action" in override:
                override["action"] = _validated_action(
                    override["action"],
                    f"override tool={override.get('tool', '?')} path={override.get('path_pattern', '?')}",
                    default="ask",
                )
        return policy if policy else _safe_resolve_default(), overrides
    except (json.JSONDecodeError, KeyError, TypeError, OSError):
        return _safe_resolve_default(), []


def _check_overrides(overrides, tool_name, tool_input):
    """Check if any override rule matches. Return action or None."""
    for override in overrides:
        if override.get("tool") != tool_name:
            continue
        path_pattern = override.get("path_pattern", "")
        file_path = tool_input.get("file_path", "")
        if path_pattern and file_path:
            from fnmatch import fnmatch

            if fnmatch(file_path, path_pattern):
                return override.get("action", "allow")
    return None


def _log_decision(plugin_data, input_data, level, action):
    """Append policy decision to audit trace.

    Side-effect isolation: failures from disk I/O (EACCES, ENOSPC, broken
    mount) or JSON serialization MUST NOT propagate to main(). Otherwise
    the top-level except in __main__ would catch them and emit "{}" — a
    "no decision" output the harness interprets as ALLOW, silently
    downgrading a deny/ask to an allow on disk-full.

    Catches OSError (disk full, EACCES, ENOENT on mount), TypeError and
    ValueError (JSON serialization of unexpected types). Broad Exception
    is deliberately avoided — KeyboardInterrupt / SystemExit must still
    propagate.
    """
    try:
        session_id = input_data.get("session_id", "unknown")
        audit_dir = os.path.join(plugin_data, "audit")
        os.makedirs(audit_dir, exist_ok=True)
        path = os.path.join(audit_dir, f"{session_id}.audit.jsonl")

        entry = {
            "type": "policy_decision",
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "session_id": session_id,
            "tool_name": input_data.get("tool_name", "unknown"),
            "level": level,
            "level_label": LEVEL_LABELS.get(level, "Unknown"),
            "action": action,
            "agent_id": input_data.get("agent_id"),
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except (OSError, TypeError, ValueError) as e:
        # stderr only — stdout is reserved for the hook's JSON contract.
        print(f"Audit log write failed: {e}", file=sys.stderr)


def _decision_json(action, level, tool_name):
    """Build the stdout JSON string for an action (deny/ask/allow/unknown).

    Pure function — no side effects. Returning the string lets main() emit
    the permission decision BEFORE any audit-write side effect, so an audit
    failure cannot displace the JSON contract with the harness.
    """
    if action == "allow":
        return "{}"
    if action == "ask":
        label = LEVEL_LABELS.get(level, "Unknown")
        return json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"L{level} ({label}): {tool_name} requires confirmation",
                }
            }
        )
    if action == "deny":
        label = LEVEL_LABELS.get(level, "Unknown")
        return json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"L{level} ({label}): {tool_name} blocked by policy",
                }
            }
        )
    # #277 R1 — unrecognized action verb (string typo, None, int, list, dict, bool).
    # Fail-closed to ask: emit the ask shape with a reason naming the unknown verb.
    # repr(action) escapes injection attempts in attacker-controlled policy.json.
    sys.stderr.write(
        f"policy_gate: unrecognized action {action!r} reached _decision_json "
        f"(level={level}, tool={tool_name!r}); defaulting to ask\n"
    )
    label = LEVEL_LABELS.get(level, "Unknown")
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": (
                    f"L{level} ({label}): {tool_name} — unrecognized policy action {action!r}, defaulting to ask"
                ),
            }
        }
    )


def main():
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if not plugin_data:
        # No plugin data dir — cannot load policy, pass through
        print("{}")
        return

    input_data = json.load(sys.stdin)
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    level = _classify_tool(tool_name, tool_input)
    policy, overrides = _load_policy(plugin_data)

    # No policy file = pass-through (opt-in design, zero impact on default sessions)
    if policy is None:
        print("{}")
        return

    # Check overrides first
    override_action = _check_overrides(overrides, tool_name, tool_input)
    if override_action:
        action = override_action
    else:
        action = policy.get(level, "ask")

    # Decide-then-side-effect: emit permission JSON before any audit write
    # so a _log_decision failure cannot displace it. Outer try is
    # belt-and-braces in case a future audit backend bypasses the inner
    # swallow in _log_decision.
    print(_decision_json(action, level, tool_name))
    try:
        _log_decision(plugin_data, input_data, level, action)
    except Exception as e:  # noqa: BLE001 — audit must not break enforcement
        print(f"Audit log write failed: {e}", file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover
    try:
        main()
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        print("{}")
    finally:
        sys.exit(0)
