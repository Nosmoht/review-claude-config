---
name: detection-rules
description: Known-critical-bug detectors for /audit-policy-compliance — encodes #39523 (bypass-permissions) and related permission-system bugs with adversarial robustness specs
last_refreshed: 2026-04-19
---

# Detection Rules

Each rule fires against either (a) the audit trace `.jsonl` already
loaded by the skill or (b) a settings layer (`settings.json`,
`settings.local.json`, `~/.claude/settings.json`) inspected during the
audit. Rules normalise input before regex match (Unicode NFC,
lowercase, whitespace collapse, comment-strip).

Source: `research/claude-code/known-issues.md` §"Detector Recipes" +
TL;DR list.

## Rule Index

| ID | Bug | Severity | Inputs |
|----|-----|----------|--------|
| BYP-1 | #39523 bypass-permissions broken on protected dirs | Critical | settings layers + trace |
| BYP-2 | #39523 PreToolUse hook `allow` followed by user prompt | Critical | trace |
| PCR-1 | #41259 settings.local.json edited but not reloaded | High | trace + settings mtime |
| MAT-1 | #46978 permission matcher fails to auto-approve glob | Medium | trace + settings.permissions |

## Input Normalisation (applied before every match)

1. Decode JSON with comment-tolerant parser (strip `//` and `/* */`
   first; raw `json.loads` chokes).
2. Unicode NFC normalisation on all string values.
3. Case-fold keys (e.g., treat `bypassPermissions`, `bypasspermissions`,
   `BYPASS_PERMISSIONS` as equivalent for detection only — original
   spelling preserved in finding output).
4. Whitespace trim + internal-collapse on string values.
5. Numeric/boolean coercion: `"true"` and `true` are equal for matching.

## BYP-1 — #39523 detector (bypass + protected dir)

**Signal:** any settings layer contains
`defaultMode: "bypassPermissions"` (case-insensitive after
normalisation) AND the trace contains ≥1 Write/Edit/MultiEdit call whose
`tool_input.file_path` matches a protected directory:

```
^(?:.*/)?(\.claude|\.git|\.vscode|\.idea|\.husky)(/|$)
```

**Finding severity:** Critical. Body: "settings layer X declares
defaultMode=bypassPermissions but Claude Code rejects writes to
protected dir Y regardless — the bypass setting is a no-op for these
paths. Audit trail: tool_call N at line L."

**Adversarial test cases (≥5 per plan P0.6):**

1. Whitespace: `"defaultMode" :  "bypassPermissions"` (extra spaces) — must match.
2. Case: `"defaultmode": "BYPASSPERMISSIONS"` — must match.
3. Unicode normalisation: `"defaultMode": "bypassPermiss\u0131ons"` (Turkish dotless i) — must NOT match (different codepoint).
4. Comment obfuscation: `"defaultMode": /* hint */ "bypassPermissions"` — strip comments then match.
5. Split-value: `"defaultMode": "bypass" + "Permissions"` (string concat in non-JSON context, e.g. JS) — must NOT match (out of detector scope; flag as JSON-syntax violation instead).
6. Path-encoding: write target `/repo/%2Egit/HEAD` (URL-encoded `.git`) — decode before regex match.

## BYP-2 — #39523 detector (hook allow → user prompt)

**Signal:** trace shows a `PreToolUse` hook returning
`{"decision": "allow"}` for tool T, followed within the same agent_id
by a `permission_prompt` notification event for the same tool. The
allow was overridden by the protected-dir guard.

**Finding severity:** Critical.

**Adversarial test cases:** allow-decision values to recognise:
`{"decision":"allow"}`, `{"decision":"approve"}`,
`{"continue":true,"reason":"approved"}`,
`{"hookSpecificOutput":{"permissionDecision":"allow"}}` (new schema),
nested allow inside `output.tool_input` (legacy double-wrap).

## PCR-1 — #41259 detector (settings cache reload)

**Signal:** trace contains an Edit/Write to `settings.local.json` or
`settings.json` at timestamp T1, followed by a tool_call at T2 > T1
that triggers a permission prompt the new settings should have allowed.
Compare the on-disk settings mtime (read at audit time) against the
in-trace permission cache version (look for `policy_version` field in
`hook_event_name == "ConfigChange"`).

**Severity:** High. Recommend session restart.

**Adversarial test cases:** Edit followed by 0 prompts (PASS — quiet
session); Edit followed by prompt for permission ALREADY in old policy
(PASS — not a drift); Edit on policy referenced via symlink (resolve
symlink before mtime check); Edit on settings.local.json that does NOT
exist before write (creation case — special-cased: cache invalidation
is implicit at process start).

## MAT-1 — #46978 detector (glob auto-approve)

**Signal:** settings.permissions contains an `allow` entry with a glob
pattern (`*`, `**`, `?`) AND the trace contains a permission prompt for
a tool/path that the glob covers.

**Severity:** Medium. Recommend either explicit per-path entry or
upgrade target CLI version.

**Adversarial test cases:** glob with character class `[abc]`; glob in
sub-key (`Bash(npm:*)` → `npm install`); negated glob `!.git/*`;
double-star path `lib/**/test.js` matched by `lib/test.js` (depends on
glob semantics — current Claude Code matcher is non-recursive single
`**`); Unicode in path (`docs/café/*` matching `docs/cafe/file.md`).

## Reporting

Each rule emits a finding with:

- `ID: BYP-1:settings.local.json:Safety/v1` (per repo finding-identity contract).
- `severity: Critical | High | Medium`.
- `evidence`: ≥1 trace line number AND ≥1 settings file path with line.
- `recommendation`: prose with at minimum the affected paths, the bug
  reference URL, and a one-line workaround.

## Disabling rules

A rule may be disabled per session via
`$CLAUDE_PLUGIN_DATA/policy.json` `disable_detection_rule: ["BYP-1"]`.
Disabled rules still run but emit `severity: Info` (audit trail
preserved); only the surfaced severity is suppressed.
