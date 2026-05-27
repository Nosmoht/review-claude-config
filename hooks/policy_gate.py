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


def _load_policy(plugin_data):
    """Load policy from file. Return None if no policy file exists (opt-in design)."""
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
                policy[int(level_str[1:])] = rule.get("action", "ask")
        overrides = data.get("overrides", [])
        return policy if policy else _resolve("DEFAULT_POLICY"), overrides
    except (json.JSONDecodeError, KeyError, TypeError):
        return _resolve("DEFAULT_POLICY"), []


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

    Pure function — no side effects. Returning the string (rather than
    printing) lets main() emit the permission decision BEFORE any
    audit-write side effect, so an audit failure cannot displace the
    JSON contract with the harness.
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
    return "{}"


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
