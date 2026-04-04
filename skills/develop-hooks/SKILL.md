---
name: develop-hooks
description: >
  Create a new Claude Code hook script and register it in hooks.json.
  Use when adding automation hooks to enforce quality gates, inject context,
  control permissions, or log agent activity.
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

Valid hook types: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `SessionStart`, `Stop`, `SubagentStart`, `SubagentStop`, `PreCompact`, `PermissionRequest`, `Notification`.

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
5. **Timeout** — default 10 seconds; max 30 seconds. Async hooks (`{"async": true}`) do not block.
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
  - `SessionStart`: `json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": <text>}})`
  - Async logging: `json.dumps({"async": true})`
  - No-op: `print("{}")`
- Safety wrapper: `try: main() except Exception: print("{}") finally: sys.exit(0)`.

Show the full script to the user. Ask: "Does this look correct? (yes/edit/cancel)"

- **yes** — Proceed to Step 5.
- **edit** — Ask what to change, regenerate, and show again.
- **cancel** — Stop without writing anything.

### 5. Generate hooks.json entry

Build the JSON entry for the hook type. For `PreToolUse`, include the `matcher` field. For other types, omit it.

Show the full updated `hooks.json` with the new entry merged in.
Ask: "Does this look correct? (yes/edit/cancel)"

### 6. Test the hook

Run a syntax check before writing any files:

```
Bash: echo '{}' | python3 hooks/<hook-name>.py
```

Report the result. If the test fails, show the error output and stop — do not proceed to Step 7.

### 7. Write files (confirmation gate)

Ask: "Write `hooks/<hook-name>.py` and update `hooks/hooks.json`? (yes/no)"

If yes:
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

Then end your response with this menu:

---
**What's next?**
1. Test the hook in a real Claude Code session
2. Develop another hook → `/develop-hooks [hook-type] <hook-name>`
3. Done

_Type a number to continue._

---

When the user responds: **1** → advise them to start a new session and observe hook output. **2** → ask for the new hook name and type, then restart from Step 1. **3** → acknowledge and stop.

## Hard Rules

- **Safety wrapper required.** Every generated hook must have `try: main() except Exception: print("{}") finally: sys.exit(0)`. Omitting this causes a failing hook to break the agent session.
- **hooks.json must remain valid JSON.** After editing, always run the Python JSON validation check in Step 7. A malformed hooks.json prevents all hooks from loading.
- **Test before write.** Step 6 (syntax/execution test) must pass before Step 7 (file write). Do not skip this step even if the script looks correct.
- **Bash restricted to python3.** The Bash tool is used only for `python3` execution: syntax checks and JSON validation. No other shell commands.
- **No overwriting existing hooks.** If `hooks/<hook-name>.py` already exists, refuse and ask for a different name.
- **Preserve existing hooks.json entries.** When adding a new entry, append within the correct section. Never remove or reorder existing entries.
- **Kebab-case hook names only.** Reject names with spaces, underscores, or uppercase characters.
