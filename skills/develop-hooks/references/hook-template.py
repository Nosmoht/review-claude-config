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
