#!/usr/bin/env python3
"""Hook template: <REPLACE with hook purpose>.

How to use this template
------------------------
1. Replace the module docstring with your hook's purpose.
2. Set Hook type, Trigger, and Output below.
3. Fill in the main() logic section.
4. Remove comment blocks that don't apply to your hook type.
5. Test: echo '{}' | python3 hooks/<your-hook-name>.py

Hook type: <PreToolUse | PostToolUse | PostToolUseFailure | SessionStart |
            Stop | SubagentStart | SubagentStop | PreCompact |
            PermissionRequest | Notification>
Trigger: <matcher regex for PreToolUse, e.g. "Edit|Write" — omit for others>
Output: <systemMessage | permissionDecision | additionalContext | {}>

Quality-gate baseline (skills/review-hook/references/hook-evaluation-guide.md)
-------------------------------------------------------------------------------
This template already satisfies the following checklist items by construction.
Edits should preserve them:

- PY-1: input from sys.stdin (line 60), not argv.
- PY-2: every code path prints valid JSON to stdout (success: line 73/77/82/91; error: try/except writes "{}" at line 99).
- PY-3: exit code 0 in finally (line 101); use sys.exit(2) only for blocking PreToolUse deny.
- PY-6: CLAUDE_PLUGIN_ROOT checked before use (line 54-57); graceful exit if absent.
- PY-7: os.path.join for file paths (line 21, 70); no string concatenation.
- PY-8: top-level try/except + finally sys.exit (line 95-101) — required for HC-3 Safety.
- HC-3: on_error behaviour defined (non-blocking via print("{}")).
- SR-1: no credential/token access in template defaults — keep that way.

Set when registering in hooks.json:
- HC-2: matcher targets a single tool name or explicit glob (no catch-all).
- HC-4: timeout reasonable for the runtime type (command ≤600s; PreToolUse blocking ≤10s).
- HC-5: description field present explaining the hook's purpose.
- HC-7: PreToolUse / Stop / SubagentStop / TaskCreated / ConfigChange — exit-code semantics handled (exit 2 blocks).

Key environment variable
------------------------
CLAUDE_PLUGIN_ROOT — absolute path to the installed plugin directory.
Use it to build paths to reference files: os.path.join(plugin_root, "hooks", "file.md")

Output formats by hook type
----------------------------
PreToolUse — inject guidance:
    {"systemMessage": "..."}

PreToolUse — deny tool call:
    {"permissionDecision": "deny", "userMessage": "reason"}

PreToolUse — allow with rewritten input:
    {"permissionDecision": "allow", "updatedInput": {...}}

PreToolUse — ask user to decide:
    {"permissionDecision": "ask", "userMessage": "reason"}

PreToolUse — defer (pause a headless/CI session at this tool boundary; v2.1.89+,
REAL but officially-undocumented — tracked anthropics/claude-code#41791; re-verify
against code.claude.com/docs/en/hooks before relying on the exact field shape):
    {"permissionDecision": "defer"}
# Resumes via:  claude -p --resume <session-id>
# GOTCHA: only works when Claude makes a SINGLE tool call in the turn —
#         a multi-tool turn cannot defer one call while leaving the rest unresolved.

SessionStart — inject session context:
    {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}

Async logging (any type, non-blocking):
    {"async": true}

No-op (any type):
    {}
"""

import json
import os
import sys


def main():
    # Access plugin root for building file paths
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        print("{}")
        return

    # Read input from stdin
    _input_data = json.load(sys.stdin)

    # --- PreToolUse: inspect tool name and file path ---
    # tool_name = _input_data.get("tool_name", "")
    # tool_input = _input_data.get("tool_input", {})
    # file_path = tool_input.get("file_path", "")

    # --- Your hook logic here ---

    # Example A: inject a system message
    # guidelines_path = os.path.join(plugin_root, "hooks", "guidelines.md")
    # with open(guidelines_path) as f:
    #     guidelines = f.read()
    # print(json.dumps({"systemMessage": guidelines}))
    # return

    # Example B: deny a tool call
    # print(json.dumps({"permissionDecision": "deny", "userMessage": "Reason"}))
    # return

    # Example C: SessionStart advisory
    # msg = "Advisory text injected at session start."
    # print(json.dumps({
    #     "hookSpecificOutput": {
    #         "hookEventName": "SessionStart",
    #         "additionalContext": msg,
    #     }
    # }))
    # return

    # Default: no-op
    print("{}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let a hook error break the agent session.
        print("{}")
    finally:
        sys.exit(0)
