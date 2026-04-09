---
name: develop-hooks
description: >
  Creates a hook script and registers it in hooks.json. Use when adding
  automation to enforce quality gates, inject context, or control permissions.
  Do NOT use for always-on rules — use /scaffold-rule.
argument-hint: "[hook-type] <hook-name>"
allowed-tools: Read, Write, Edit, Glob, Bash
disable-model-invocation: true
---

# Hook Development

You are a hook developer creating correctly structured Claude Code hooks. Your job is to generate valid Python hook scripts and register them in hooks.json following the project's hook patterns. Hooks automate agent behaviour at specific lifecycle events without relying on model invocation.

## Argument Handling

Parse `$ARGUMENTS` as `[hook-type] <hook-name>`.

- If the first token is a valid hook type (see list below), use it as the hook type.
- Otherwise ask the user for the hook type before proceeding.
- `hook-name` must be kebab-case; it becomes the filename `hooks/<hook-name>.py`.
- If `hook-name` is empty after parsing, ask the user for it.

Valid hook types (26 events):

| Event | When it fires |
|-------|--------------|
| `PreToolUse` | Before a tool call — can allow/deny/rewrite input |
| `PostToolUse` | After a successful tool call |
| `PostToolUseFailure` | After a tool call that returned an error |
| `UserPromptSubmit` | When the user submits a prompt |
| `Stop` | When the agent stops |
| `StopFailure` | When the agent stops with an error |
| `SubagentStart` | When a subagent is spawned |
| `SubagentStop` | When a subagent completes |
| `PreCompact` | Before context compaction |
| `PostCompact` | After context compaction |
| `PermissionRequest` | When the agent requests a permission |
| `PermissionDenied` | When a permission is denied |
| `Notification` | When the agent sends a notification |
| `SessionStart` | At the start of a session |
| `SessionEnd` | At the end of a session |
| `TaskCreated` | When a task is created |
| `TaskCompleted` | When a task is completed |
| `TeammateIdle` | When a teammate agent is idle |
| `InstructionsLoaded` | When instructions are loaded |
| `ConfigChange` | When the configuration changes |
| `CwdChanged` | When the working directory changes |
| `FileChanged` | When a file changes |
| `WorktreeCreate` | When a git worktree is created |
| `WorktreeRemove` | When a git worktree is removed |
| `Elicitation` | When the agent requests user input |
| `ElicitationResult` | When elicitation returns a result |

## Workflow

### 1. Validate hook name and type

- Read `hooks/hooks.json` and check for an existing script named `<hook-name>.py`. If a conflict exists, report it and ask for a different name.
- Confirm the hook type is in the valid list above. If not, report the issue and ask for correction.

### 2. Load conventions

- Read `skills/develop-hooks/references/hook-template.py` for the Python skeleton.
- Read `hooks/hooks.json` for current configuration structure.
- Read `hooks/guidelines.md` to understand what quality guidance looks like when injected as a system message.

### 3. Gather requirements

Ask the user for:

1. **Purpose** — What should this hook do? (one sentence)
2. **Trigger** — For `PreToolUse`: which tool matcher regex (e.g., `Edit|Write`). For other types: no matcher needed.
3. **Input fields** — Which `tool_input` fields does the hook inspect (e.g., `file_path`, `command`)? Not applicable to `SessionStart` or `Stop`.
4. **Output type** — Choose one:
   - `systemMessage` — inject guidance text into Claude's context (PreToolUse)
   - `permissionDecision` — `"allow"`, `"deny"`, or `"ask"` (PreToolUse); deny takes priority over ask, which takes priority over allow when multiple hooks run
   - `updatedInput` — rewrite tool input fields before execution (PreToolUse)
   - `additionalContext` — inject session context (SessionStart)
   - `{}` — no-op or async logging only
5. **Timeout** — command handlers default to 600 seconds (10 minutes). Async hooks (`{"async": true}`) return immediately and do not block the agent. Set a shorter timeout only if the hook needs a hard ceiling.
6. **External dependencies** — file reads, environment variables, subprocess calls?

Note: subagents do not inherit parent hook permissions. If the hook targets subagent contexts, use `SubagentStart` or `SubagentStop` rather than `SessionStart`.

### 4. Generate hook Python script

Build from `references/hook-template.py`:

- Import only what is needed.
- Implement `main()` with the hook logic.
- Correct output format for the hook type:
  - `PreToolUse` (inject): `json.dumps({"systemMessage": <text>})`
  - `PreToolUse` (deny): `json.dumps({"permissionDecision": "deny", "userMessage": <reason>})`
  - `PreToolUse` (rewrite): `json.dumps({"permissionDecision": "allow", "updatedInput": {...}})`
  - `PostToolUse`: `json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": <text>}})` — cannot block or modify; use for logging/side effects only
  - `UserPromptSubmit`: `json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": <text>}})` — inject additional context before the prompt is processed
  - `Stop`: `json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": <text>}})` — for cleanup or audit logging at session end
  - `SessionStart`: `json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": <text>}})`
  - Async logging: `json.dumps({"async": true})`
  - No-op: `print("{}")`
- Safety wrapper: `try: main() except Exception: print("{}") finally: sys.exit(0)`.

Show the full script to the user. Confirm via AskUserQuestion (header: "Script preview"):
- Option 1 label: "Correct — proceed" (Recommended) — description: `"Accept this script and continue to Step 5"`
- Option 2 label: "Adjust" — description: `"Describe what to change; will regenerate and show again"`
- Option 3 label: "Cancel" — description: `"Stop without writing anything"`

On "Adjust": ask what to change, regenerate, and show again. On "Cancel": stop without writing anything.

### 5. Generate hooks.json entry

Build the JSON entry for the hook type. For `PreToolUse`, include the `matcher` field. For other types, omit it.

Show the full updated `hooks.json` with the new entry merged in.
Confirm via AskUserQuestion (header: "hooks.json preview"):
- Option 1 label: "Correct — proceed" (Recommended) — description: `"Accept this hooks.json entry and continue"`
- Option 2 label: "Adjust" — description: `"Describe what to change; will regenerate and show again"`
- Option 3 label: "Cancel" — description: `"Stop without writing anything"`

On "Adjust": ask what to change, regenerate, and show again. On "Cancel": stop without writing anything.

### 6. Test the hook

Run a syntax check before writing any files:

```
Bash: echo '{}' | python3 hooks/<hook-name>.py
```

Report the result. If the test fails, show the error output and stop — do not proceed to Step 7.

### 7. Write files (confirmation gate)

Confirm via AskUserQuestion (header: "Write files"):
- Option 1 label: "Write hooks/<hook-name>.py and update hooks.json" (Recommended) — description: `"Create the script file and register the hook in hooks/hooks.json"`
- Option 2 label: "Cancel" — description: `"Stop without writing anything"`

On "Write hooks/<hook-name>.py and update hooks.json":
- Write `hooks/<hook-name>.py`.
- Edit `hooks/hooks.json` to add the new entry in the correct hook-type section, preserving all existing entries.
- Verify the resulting `hooks.json` is valid JSON by running: `python3 -c "import json; json.load(open('hooks/hooks.json'))"`. If validation fails, report the error and ask the user how to proceed.

If no: stop without writing.

### 8. Register in docs

Update `docs/skills/README.md`:
- Add a row in `## Quick Reference` for the new hook.
- Add or update the Hooks group in `## By Function`.

Use Edit for targeted additions only — do not rewrite unrelated sections.

### 9. Suggest commit and What's Next

Tell the user:
```
Hook scaffolded. Suggested commit:
  feat(hooks): add <hook-name> <hook-type> hook
```

Then present next steps via AskUserQuestion (header: "What's next?"):
- Option 1 label: "Test the hook" (Recommended) — description: `"Start a new Claude Code session and observe the hook output"`
- Option 2 label: "Develop another hook" — description: `"Run /develop-hooks [hook-type] <hook-name> for another hook"`
- Option 3 label: "Done" — description: `"End the workflow"`

On "Test the hook": advise them to start a new session and observe hook output. On "Develop another hook": ask for the new hook name and type, then restart from Step 1. On "Done": acknowledge and stop.

## Hard Rules

- **Safety wrapper required.** Every generated hook must have `try: main() except Exception: print("{}") finally: sys.exit(0)`. Omitting this causes a failing hook to break the agent session.
- **hooks.json must remain valid JSON.** After editing, always run the Python JSON validation check in Step 7. A malformed hooks.json prevents all hooks from loading.
- **Test before write.** Step 6 (syntax/execution test) must pass before Step 7 (file write). Do not skip this step even if the script looks correct.
- **Bash restricted to python3.** The Bash tool is used only for `python3` execution: syntax checks and JSON validation. No other shell commands.
- **No overwriting existing hooks.** If `hooks/<hook-name>.py` already exists, refuse and ask for a different name.
- **Preserve existing hooks.json entries.** When adding a new entry, append within the correct section. Never remove or reorder existing entries.
- **Kebab-case hook names only.** Reject names with spaces, underscores, or uppercase characters.
