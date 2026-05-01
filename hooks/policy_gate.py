#!/usr/bin/env python3
"""PreToolUse hook: classify tool calls by action level and enforce policy.

Hook type: PreToolUse
Trigger: (all tools — no matcher, so every tool call is evaluated)
Output: permissionDecision (allow/ask/deny) based on action classification

Reads policy from $CLAUDE_PLUGIN_DATA/policy.json if available.
Falls back to default policy: L1-L3 allow, L4 ask, L5 deny.
Also logs the policy decision to the audit trace.
"""

import datetime
import json
import os
import re
import sys

# Tool-to-level mapping (L1=read, L2=analyze, L3=recommend, L4=act, L5=irreversible)
TOOL_LEVELS = {
    "Read": 1,
    "Glob": 1,
    "Grep": 2,
    "WebSearch": 2,
    "WebFetch": 2,
    "AskUserQuestion": 3,
    "Edit": 4,
    "Write": 4,
    "Bash": 4,
    "Agent": 4,
    "MultiEdit": 4,
    "NotebookEdit": 4,
}

# Bash patterns that escalate L4 → L5
L5_BASH_PATTERNS = [
    r"\brm\s+-(r|rf|fr)\b",
    r"\bgit\s+push\s+--force\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bdocker\s+rm\b",
    r"\bkubectl\s+delete\b",
    r"\bDROP\s+TABLE\b",
    r"\bDELETE\s+FROM\b",
    r"\b(deploy|publish|release)\b",
]

# Default policy: level → action
DEFAULT_POLICY = {
    1: "allow",
    2: "allow",
    3: "allow",
    4: "ask",
    5: "deny",
}

LEVEL_LABELS = {1: "Read", 2: "Analyze", 3: "Recommend", 4: "Act", 5: "Irreversible"}

# MCP tool name patterns — matched on the suffix after the last '__' separator.
# An L1 *shape* (list_/get_/retrieve_/search_ prefix or _read suffix) is only
# honored when no token in the suffix is an L4 mutation verb. Token matching
# (split on '_') avoids two substring-collision classes:
#   - 'request' inside pull_request_read / list_pull_requests is a noun, not
#     the HTTP verb. Token split keeps 'request'-the-noun distinct from a
#     mutation verb of the same letters.
#   - 'read' inside ready_to_send / thread_id is a noun fragment, not the
#     read verb — token split prevents these collisions in either direction.
# It also guards against compound idioms (get_or_create_thing, list_and_delete,
# get_and_set_label) that prefix matching alone would flip to L1. Anything not
# matching the L1 contract falls back to L4 conservatively.
_MCP_L1_PREFIXES = ("list_", "get_", "retrieve_", "search_")
_MCP_L4_VERBS = frozenset(
    {
        "create",
        "update",
        "delete",
        "archive",
        "unarchive",
        "remove",
        "transfer",
        "assign",
        "merge",
        "push",
        "fork",
        "write",
        # Real mutation verbs that surfaced in round-2 review — not all are in
        # the current GitHub/Plane MCP inventory, but they are common API shapes
        # ('set_*', 'rotate_*', 'revoke_*', 'cancel_*') worth blocking before
        # they appear, so the conservative fallback does not have to carry the
        # whole burden.
        "set",
        "rotate",
        "revoke",
        "destroy",
        "patch",
        "replace",
        "purge",
        "disable",
        "cancel",
        "close",
    }
)


def _classify_mcp_tool(tool_name):
    """Classify an mcp__ tool by name pattern. Default L4 for unknown suffixes."""
    if "__" not in tool_name:
        return 4  # malformed name — conservative fallback
    suffix = tool_name.split("__")[-1]
    is_l1_shape = any(suffix.startswith(p) for p in _MCP_L1_PREFIXES) or suffix.endswith("_read")
    has_l4_verb = bool(set(suffix.split("_")) & _MCP_L4_VERBS)
    if is_l1_shape and not has_l4_verb:
        return 1
    return 4


def _classify_tool(tool_name, tool_input):
    """Return authorization level (1-5) for a tool call."""
    level = TOOL_LEVELS.get(tool_name, 4)  # unknown tools default to L4

    # MCP tools: pattern-based classification (reads vs mutations vs unknown)
    if tool_name.startswith("mcp__"):
        level = _classify_mcp_tool(tool_name)

    # Bash escalation check
    if tool_name == "Bash" and level == 4:
        command = tool_input.get("command", "")
        for pattern in L5_BASH_PATTERNS:
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
        return policy if policy else DEFAULT_POLICY, overrides
    except (json.JSONDecodeError, KeyError, TypeError):
        return DEFAULT_POLICY, []


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
    """Append policy decision to audit trace."""
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

    # Log the decision to audit trace
    _log_decision(plugin_data, input_data, level, action)

    if action == "allow":
        print("{}")
    elif action == "ask":
        label = LEVEL_LABELS.get(level, "Unknown")
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "ask",
                        "permissionDecisionReason": f"L{level} ({label}): {tool_name} requires confirmation",
                    }
                }
            )
        )
    elif action == "deny":
        label = LEVEL_LABELS.get(level, "Unknown")
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": f"L{level} ({label}): {tool_name} blocked by policy",
                    }
                }
            )
        )
    else:
        print("{}")


if __name__ == "__main__":  # pragma: no cover
    try:
        main()
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        print("{}")
    finally:
        sys.exit(0)
