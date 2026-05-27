---
name: develop-hooks
description: >
  Creates a hook script and registers it in `hooks/hooks.json`. Triggered
  manually via `/develop-hooks [hook-type] <hook-name>`. Use when authoring
  files under `hooks/` for events PreToolUse, PostToolUse, SubagentStart,
  SubagentStop, or SessionEnd, or when `hooks/hooks.json` needs a new entry.
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

### 6. Test the hook and run quality preflight

Run a syntax check before writing any files:

```
Bash: echo '{}' | python3 hooks/<hook-name>.py
```

Then run preflight against `/review-hook` checklist IDs (see
`skills/review-hook/references/hook-evaluation-guide.md`):

- **HC-1 (event)** — confirm the chosen event is in the 26-event catalog; reject `unknown_event`.
- **HC-2 (matcher)** — for `PreToolUse`, the matcher targets a single tool name or explicit glob; reject catch-all `.*`.
- **HC-4 (timeout)** — `command` runtime cap 600 s; `prompt`/`http` 30 s; `agent` 60 s; PreToolUse blocking ≤10 s. Set explicitly when shorter than default.
- **HC-5 (description)** — `description` field in hooks.json explains the hook's purpose in one sentence.
- **HC-7 (blocking exit code)** — for events with `Blocking: Yes` (PreToolUse, Stop, SubagentStop, TaskCreated, ConfigChange), confirm exit-code semantics are handled (exit 2 blocks; non-blocking events ignore exit 2).
- **HC-8 (CLI version)** — Q1-2026 events (`PostToolUseFailure` v2.1.76; `CwdChanged`/`FileChanged` v2.1.83; `TaskCreated` v2.1.84; `PermissionDenied` v2.1.89) require CLI ≥ that release.
- **PY-2 (stdout JSON)** — verify the test from above emits valid JSON; no extraneous stderr that #34713 could mislabel as a Hook Error (BUG-1).
- **PY-8 (safety wrapper)** — confirm the generated script has the `try: main() except Exception: print("{}") finally: sys.exit(0)` block.
- **SR-1, SR-5 (Safety)** — no credentials/tokens accessed or logged; hook does not modify the files it is triggered on.

Report the result of each. If the syntax check fails or any FAIL preflight check is unresolved, show the error output and stop — do not proceed to Step 7.

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

## Quality measurement (mandatory before Step 9)

Per [`docs/skill-verification-architecture.md`](../../docs/skill-verification-architecture.md) (deep-research retrofit 2026-05-26), SCAFFOLD-class verification is deterministic — `make validate` exit-0 plus idempotency plus the safety-wrapper + output-shape predicate sweep plus the sensitive-content sweep is the sufficient verification primitive for this output class. Adversarial-critic (Layer B) and binary-rubric (Layer C) layers were dropped because the scaffolder's contract is "did you produce a syntactically valid hook script with the safety wrapper, output shape matching the event type, and a matching `hooks.json` registration," not "is this a high-quality hook" — quality assessment belongs in `/review-hook`, not here. Only Layer A (mechanical invariants) remains; the companion-artifact predicate is load-bearing because F6 (script-without-registration) is this skill's dominant failure class.

After Step 7 writes both artifacts and before Step 8 doc registration, record the artifact paths, the hook name, and the chosen hook type for the verification layer:

```bash
TMPDIR=$(mktemp -d -t develop-hooks-XXXX)
PROMISED="$TMPDIR/promised.txt"        # two absolute paths: hooks/<name>.py and hooks/hooks.json
NAME_FILE="$TMPDIR/name.txt"           # the kebab-case hook name from Step 1
HOOKTYPE_FILE="$TMPDIR/hooktype.txt"   # exactly one of the valid hook events (PreToolUse, PostToolUse, ...)
# Write the resolved hooks/<name>.py absolute path AND hooks/hooks.json absolute path to $PROMISED.
# Write the kebab-case hook name from Step 1 to $NAME_FILE.
# Write the hook event token from Step 1 to $HOOKTYPE_FILE.
```

### Pipeline — Layer A (mechanical invariants, deterministic, fail-fast)

Run all five metrics. Any `STRICT` non-zero exit → abort and report; `SOFT` deltas → log and surface to the user, do not auto-overwrite.

**A.1 STRICT — both promised files exist, non-empty, and hooks.json contains the new entry.** Companion-completeness is STRICT-dimensioned 2 (F6 — the dominant failure class for this skill).

```bash
fail=0
NAME=$(cat "$NAME_FILE")
HOOKTYPE=$(cat "$HOOKTYPE_FILE")
while IFS= read -r p; do
  if [ ! -s "$p" ]; then
    echo "STRICT FAIL existence $p (missing or empty)"
    fail=$((fail+1))
  fi
done < "$PROMISED"
# Confirm hooks.json contains an entry whose command references <name>.py
HOOKS_JSON=$(grep -E 'hooks\.json$' "$PROMISED" | head -1)
python3 -c "
import json, sys
d = json.load(open('$HOOKS_JSON'))
needle = '$NAME.py'
events = d.get('hooks', {})
found = False
for ev, entries in events.items():
    for entry in entries:
        for h in entry.get('hooks', []):
            if needle in (h.get('command') or ''):
                found = True
sys.exit(0 if found else 1)
" || { echo "STRICT FAIL entry-missing hooks.json has no entry referencing $NAME.py"; fail=$((fail+1)); }
```

**A.2 STRICT — `make validate` exits 0.** Runs the full chain: ruff lint, ruff format, JSON Schema, token budget, description-graph regression, pytest. A malformed `hooks.json` (invalid JSON) or a script that fails ruff lint will fail here.

```bash
( cd "$REPO_ROOT" && make validate ) > "$TMPDIR/make-validate.log" 2>&1
mv_exit=$?
[ $mv_exit -ne 0 ] && { echo "STRICT FAIL make-validate exit=$mv_exit"; fail=$((fail+1)); }
```

Additionally assert the safety wrapper AND hook-type / output-shape pairing on the generated script:

```bash
SCRIPT=$(grep -E '\.py$' "$PROMISED" | head -1)
python3 - "$SCRIPT" "$HOOKTYPE_FILE" <<'PY'
import re, sys
script = open(sys.argv[1]).read()
hooktype = open(sys.argv[2]).read().strip()
fail = 0
# Safety wrapper: try / except Exception / sys.exit(0) (Hard Rule)
if not re.search(r"\btry\s*:", script):
    print("STRICT FAIL safety-wrapper missing 'try:' block"); fail += 1
if not re.search(r"\bexcept\s+Exception\b", script):
    print("STRICT FAIL safety-wrapper missing 'except Exception'"); fail += 1
if not re.search(r"\bsys\.exit\s*\(\s*0\s*\)", script):
    print("STRICT FAIL safety-wrapper missing 'sys.exit(0)'"); fail += 1
# main() function present
if not re.search(r"\bdef\s+main\s*\(", script):
    print("STRICT FAIL structure missing 'def main('"); fail += 1
# Hook-type / output-shape pairing
if hooktype == "PreToolUse":
    # PreToolUse must emit one of: systemMessage, permissionDecision, updatedInput
    if not re.search(r"systemMessage|permissionDecision|updatedInput", script):
        print(f"STRICT FAIL output-shape PreToolUse must emit systemMessage/permissionDecision/updatedInput"); fail += 1
elif hooktype in ("PostToolUse", "UserPromptSubmit", "Stop", "SessionStart"):
    # These hook events emit hookSpecificOutput with matching hookEventName
    pat = rf'hookEventName.*{re.escape(hooktype)}'
    if not (re.search(r"hookSpecificOutput", script) and re.search(pat, script)):
        # Allow async-only or no-op shapes
        if not re.search(r'"async"\s*:\s*true|print\(\s*["\']\{\}["\']', script):
            print(f"STRICT FAIL output-shape {hooktype} must emit hookSpecificOutput with hookEventName={hooktype}, or async/no-op"); fail += 1
sys.exit(1 if fail else 0)
PY
```

**A.3 STRICT — sensitive-content sweep on both written artifacts.** Hook scripts (`*.py`) and `hooks.json` are NOT in `block-sensitive-content.sh`'s doc-class scope, so the user-global PreToolUse hook does NOT enforce home-path / RFC1918 / literal-secret patterns here — the sweep runs in this layer. Source the home-path regex set from `hooks/block-sensitive-content.sh` at runtime (do NOT duplicate literals here).

```bash
python3 - "$PROMISED" "$HOOK_HOME_PATTERNS_FILE" <<'PY'
import re, sys, pathlib
home_patterns = [line.strip() for line in open(sys.argv[2]) if line.strip()]
RFC1918 = r"\b(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)[0-9.]+\b"
LITERAL_SECRET = r'"(?:[A-Za-z_]*(?:TOKEN|SECRET|KEY|PASSWORD|PASSWD|PAT|APIKEY|ACCESS)[A-Za-z_]*)"\s*:\s*"(?!\$\{)[^"]{4,}"'
GH_PAT = r'\b(ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}\b'
JWT = r'\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b'
fail = 0
for line in open(sys.argv[1]):
    p = pathlib.Path(line.strip())
    if not p.exists() or not p.is_file(): continue
    t = p.read_text(errors="replace")
    for pat in home_patterns:
        if re.search(pat, t):
            print(f"STRICT FAIL home-path-leak {p} pattern={pat}"); fail += 1
    if re.search(RFC1918, t):
        print(f"STRICT FAIL rfc1918-leak {p}"); fail += 1
    if p.suffix == ".json" and re.search(LITERAL_SECRET, t):
        print(f"STRICT FAIL literal-secret {p}"); fail += 1
    if re.search(GH_PAT, t):
        print(f"STRICT FAIL github-pat-shape {p}"); fail += 1
    if re.search(JWT, t):
        print(f"STRICT FAIL jwt-shape {p}"); fail += 1
sys.exit(1 if fail else 0)
PY
```

**A.4 STRICT — path-placement matches the script and hooks.json predicates.**

```bash
while IFS= read -r p; do
  case "$p" in
    */hooks/[a-z]*-[a-z0-9-]*.py|*/hooks/[a-z][a-z0-9-]*.py) ;;
    */hooks/hooks.json) ;;
    *) echo "STRICT FAIL path-placement $p (not hooks/<kebab-name>.py or hooks/hooks.json)"; fail=$((fail+1)) ;;
  esac
done < "$PROMISED"
```

**A.5 SOFT — doc-registration count.** The skill's Step 8 edits `docs/skills/README.md`. Absence is a SOFT warning the user must acknowledge — registration-skip may be legitimate for transient/experimental hooks. Surfaces in the Step 9 success notice as a warning, not a STRICT fail.

What each metric catches:

| Metric | Catches |
|---|---|
| A.1 file-existence + entry-presence | F1, F6 |
| A.2 `make validate` + safety-wrapper + output-shape | F1, F2 |
| A.3 sensitive-content sweep | F7 |
| A.4 path-placement | F5 |
| A.5 doc-registration count | F6 (soft) |

### Reconciliation outcomes

- **All STRICT pass (Layer A: A.1 both-files + entry-presence, A.2 `make validate` + safety-wrapper + output-shape, A.3 sensitive-content sweep, A.4 path predicates)** → SCAFFOLD reported successful; proceed to Step 8 doc registration and Step 9 commit suggestion.
- **Any STRICT fail** → restore inline. For safety-wrapper / output-shape / path issues the fix is mechanical (regenerate the script with the missing wrapper, switch the output shape to match the event type, move/rename the file, redact). Max **2 iterations**, then surface to the user with the exact failing predicate + the candidate diff. Do NOT silently overwrite or hide the failure. The 2-iteration cap mirrors `rules/agentic-workflow.md §"Loop-on-symptom — stop after three"` — by iteration 3 the frame is wrong, not the artifact.
- **Only SOFT warnings (e.g. A.5 doc-registration skipped)** → report in the Step 9 success notice but proceed. The Step 5 + Step 7 AskUserQuestion preview gates are the final human-glance opportunities.

### Acknowledged residuals (the pipeline does NOT catch these)

The deterministic Layer A checks bound **structural correctness and safety-wrapper presence**, not **quality**. Semantic defects (wrong-predicate-with-valid-form, matcher-regex overreach, runtime-credential drift, hooks.json section misordering) and template-drift detection live in `/review-hook` and the 90-day baseline-refresh cadence. See [`docs/skill-verification-architecture.md`](../../docs/skill-verification-architecture.md) for the full residual catalog and per-output-class form mapping rationale. Two representative residuals worth surfacing at the Step 9 notice:

1. **Semantic-wrong hook logic with valid form.** A script whose body is grammatically Python, has the safety wrapper, and emits the right output shape, but implements the wrong predicate. All Layer A checks pass; only the Step 5 human preview gate catches.
2. **Matcher-regex overreach.** A `PreToolUse` hook's `matcher` field captures more tools than intended (e.g. `.*` instead of `Edit|Write`). Detected only by manual review of the matcher pattern at the Step 5 preview gate.

## Hard Rules

- **Safety wrapper required.** Every generated hook must have `try: main() except Exception: print("{}") finally: sys.exit(0)`. Omitting this causes a failing hook to break the agent session.
- **hooks.json must remain valid JSON.** After editing, always run the Python JSON validation check in Step 7. A malformed hooks.json prevents all hooks from loading.
- **Test before write.** Step 6 (syntax/execution test) must pass before Step 7 (file write). Do not skip this step even if the script looks correct.
- **Bash restricted to python3.** The Bash tool is used only for `python3` execution: syntax checks and JSON validation. No other shell commands.
- **No overwriting existing hooks.** If `hooks/<hook-name>.py` already exists, refuse and ask for a different name.
- **Preserve existing hooks.json entries.** When adding a new entry, append within the correct section. Never remove or reorder existing entries.
- **Kebab-case hook names only.** Reject names with spaces, underscores, or uppercase characters.
