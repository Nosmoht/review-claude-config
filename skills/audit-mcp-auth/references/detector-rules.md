---
name: detector-rules
description: #45551 detector rules for MCP OAuth credential-store corruption (macOS Team-plan race) with adversarial robustness specs
last_refreshed: 2026-04-19
---

# MCP-Auth Detector Rules

Three detectors covering the #45551 race-condition preconditions. Each
detector ships with input-normalisation steps and ≥5 adversarial test
cases per repo P0.6 robustness contract.

Source: `research/claude-code/known-issues.md` §"Detector Recipes" +
issue #45551 reproduction notes.

## Input Normalisation

1. Bash command output: trim trailing newlines, decode UTF-8 errors as `replace`.
2. Keychain entry contents: pass through `json.loads` after stripping any leading shell-prompt artefacts.
3. Process list parsing: split each line on whitespace, take last fields as command path; resolve symlinks before counting (so `/usr/bin/claude` and `/opt/homebrew/bin/claude` symlinked to the same binary count as one binary class, but distinct PIDs).
4. macOS version normalisation: `sw_vers -productVersion` → tuple `(major, minor, patch)`; comparisons numeric not lexicographic.

## KCH-1 — Keychain entry size approaching truncation

**Signal:** keychain entry contents `wc -c > 2010` bytes.

**Severity:** High if 2010 < size ≤ 2200 (approaching truncation);
Critical if size > 2200 (truncation likely already occurred — JSON parse
likely fails downstream).

**Adversarial test cases:**

1. Exactly 2010 bytes — no fire.
2. 2011 bytes — fire High.
3. 2050 bytes with valid JSON — fire High but JSON parse succeeds; surface size warning only.
4. 2200 bytes — boundary High → Critical transition.
5. 2300 bytes with valid JSON (compressed payload) — fire Critical even when parse succeeds (size alone is the signal).
6. 1999 bytes after Unicode-NFC expansion (was 1990 NFD) — normalise first.

## KCH-2 — Keychain JSON parse failure or missing key

**Signal:** keychain contents either:

- Fail JSON parse (bracket mismatch, truncated string, etc.).
- Parse but lack `claudeAiOauth` key.

**Severity:** Critical (active corruption signal).

**Adversarial test cases:**

1. Single trailing comma (`{"x":1,}`) — Python `json.loads` rejects → fire.
2. Unclosed string (`{"x":"abc`) — fire.
3. Empty object `{}` — fire (missing key).
4. Object with `claudeAIoauth` (case-mismatch typo) — fire.
5. Nested `{"data": {"claudeAiOauth": {...}}}` — does NOT fire (key present at any depth counts as present per current implementation; documented for reviewer awareness).
6. Object with key but null value `{"claudeAiOauth": null}` — fire (key without payload is corruption-equivalent).

## SES-1 — Session multiplicity above corruption threshold

**Signal:** count of running `claude` processes (excluding helper
binaries identified by absolute path) > 5.

**Severity:** High when 5 < count ≤ 10; Critical when count > 10.

**Adversarial test cases:**

1. 5 sessions — no fire.
2. 6 sessions — fire High.
3. 11 sessions — fire Critical.
4. 6 sessions where 2 are zombie (PID exists but parent reaped) — count zombies separately, only count live sessions.
5. 6 sessions where 1 is `claude-code-helper` (helper binary path) — exclude helper, count = 5 → no fire.
6. 6 sessions on non-Team plan (no shared keychain race possible) — still fire SES-1 with note "applies only to Team plan; verify plan tier".

## Reporting Format

Each fire produces a finding with:

- `ID: KCH-1:macos-keychain:Safety/v1` (per repo finding-identity contract).
- `severity`: as defined above.
- `evidence`: redacted snippet (≤200 base64-encoded bytes) for KCH-*; PID list for SES-*.
- `recommendation`: link to issue #45551 + concrete next step ("rotate via /logout + /login before truncation"; "throttle concurrent sessions to ≤5").

## Disabling rules

`$CLAUDE_PLUGIN_DATA/policy.json` `disable_detection_rule: ["KCH-1"]`
suppresses surfaced severity but keeps audit trail (Info-level only).

## Cross-references

- Bug context: `research/claude-code/known-issues.md` §"#45551 — MCP
  OAuth credential-store race"
- Sister detector: `skills/audit-policy-compliance/references/detection-rules.md` (#39523 family)
