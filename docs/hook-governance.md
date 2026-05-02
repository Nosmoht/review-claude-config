---
name: hook-governance
description: Per-hook classification table and audit-data retention/redaction policy for all hooks registered in hooks/hooks.json
last_refreshed: 2026-05-02
owner: maintainer
---

# Hook Governance

This document classifies every hook registered in `hooks/hooks.json` by risk, data sensitivity, retention period, and owner. It also defines the redaction rules applied before audit data is persisted and the retention tiers in force today.

Context for the overall runtime audit design (policy-gate opt-in rationale, audit-logger always-on decision, pattern-based MCP classification) lives in [docs/runtime-audit-design-rationale.md](runtime-audit-design-rationale.md). This document is the operational companion: it answers "what data does each hook touch, and for how long does it stay?"

## Hook Classification

Column definitions:

- **class** — `block` (can deny a tool call), `warn` (injects advisory; never denies), `observe` (writes audit data; no influence on tool execution), `summarize` (aggregates session metrics; no influence on tool execution)
- **risk** — `low` / `medium` / `high`
- **data_sensitivity** — `none` (no data persisted), `metadata` (event ids, timestamps, classifications), `content` (file paths, cwd, tool names), `secret-risk` (tokens, passwords — requires redaction + sunset date in notes)
- **retention** — concrete max-age: `30 days rolling`, `session-only` (process memory + stdout/stderr only), `none` (no persistence)

| Hook | Script | class | risk | data_sensitivity | retention | owner | notes |
|---|---|---|---|---|---|---|---|
| PreToolUse | skill_quality_gate.py | warn | low | metadata | session-only | maintainer | Advisory injection (`systemMessage`); never blocks. Matcher = Edit/Write/MultiEdit on skill/agent/rule files. |
| PreToolUse | policy_gate.py | block | medium | metadata | 30 days rolling | maintainer | **Opt-in**: pass-through unless `$CLAUDE_PLUGIN_DATA/policy.json` exists. ALSO writes `policy_decision` entries to audit JSONL (audit-writer side-effect). |
| PostToolUse | audit_logger.py | observe | low | content | 30 days rolling | maintainer | Tool input SHA-256 hashed; `cwd` $HOME-redacted per Redaction Rules below. |
| PostToolUseFailure | audit_logger.py | observe | low | content | 30 days rolling | maintainer | Same writer as PostToolUse; `success: false` flag. |
| SubagentStart | delegation_tracker.py | observe | low | metadata | 30 days rolling | maintainer | Subagent type + parent session id; no tool inputs. |
| SubagentStop | delegation_tracker.py | observe | low | metadata | 30 days rolling | maintainer | Termination event; duration + status. |
| SessionStart | session_check.py | observe | low | none | session-only | maintainer | Reference-freshness check; emits stats to stdout, no JSONL write. |
| StopFailure | error_tracker.py | observe | low | metadata | 30 days rolling | maintainer | API errors (rate limit, auth, server); error classification only, no payload. |
| SessionEnd | session_audit.py | summarize | low | metadata | 30 days rolling | maintainer | Aggregate session metrics; appended to JSONL. |
| SessionEnd | audit_rotator.py | observe | none | none | none | maintainer | Rotates JSONL when >10 MB (3-generation ladder); does not write data, only manages files. |

## Redaction Rules

These rules apply to data written to `$CLAUDE_PLUGIN_DATA/audit/` JSONL by any hook classified `data_sensitivity: content` or higher. Rules are applied before the JSONL line is flushed.

### Implemented (PR #126)

| Field | Rule | Implementation |
|---|---|---|
| `cwd` in every `tool_call` entry | Leading `$HOME` prefix replaced with `~`. Boundary-safe: `$HOME/foo` becomes `~/foo`, but `${HOME}extended/x` is NOT replaced (path-component boundary check via `os.sep`). No-op when `$HOME` is unset, `/`, or `~` itself. | `hooks/audit_logger.py` — `_redact_home()` + `_REDACT_ENABLED` guard |
| `tool_input` in every `tool_call` entry | SHA-256 hash (already implemented since initial release). | `hooks/audit_logger.py` — `_hash_input()` |

### Policy-declared, not yet implemented (follow-up PR)

| Field | Rule |
|---|---|
| `.env*` paths anywhere in a string field | Replace with empty string `""`. Prevents accidental logging of `.env` file paths that might appear in `cwd` or other fields. |
| Strings matching secret-pattern regex `(?i)(api[_-]?key\|token\|secret\|password\|bearer)\s*[:=]\s*\S+` | Replace with `"<REDACTED>"`. Catches inline credential assignments. |

### Known limitations

- NFC/NFD unicode normalization: if `$HOME` contains composed vs decomposed unicode characters that differ from the value in the `cwd` string, the prefix match fails silently (no-match, no replacement). Best-effort prefix matching only.
- Case-insensitive filesystems (macOS, Windows): redaction uses exact byte comparison. On case-insensitive mounts where `$HOME` and `cwd` differ only in case, the match fails. Out of scope for this PR (CI is POSIX-only).
- Trailing-slash `$HOME`: `os.path.expanduser("~")` never returns a trailing slash on POSIX (verified in CPython source); this edge is documented for completeness but is not a live issue.
- Symlink resolution: `_redact_home` does not resolve symlinks. If `cwd` is a symlink target that does not share a byte-prefix with `$HOME`, the match fails.

## Retention

Three retention tiers are in use:

| Tier | Definition | Enforced by |
|---|---|---|
| `30 days rolling` | JSONL rotated when the active file exceeds ~10 MB; 3 generations kept; effective window is ~30 days for typical session volume. | `hooks/audit_rotator.py` (SessionEnd trigger, 3-generation ladder with atomic replace + fcntl lock) |
| `session-only` | Data lives in process memory, stdout, or stderr of the hook process. No file written. Disappears when the hook process exits. | Architecture (no write call in the hook script) |
| `none` | Hook writes nothing and manages no persistent state. Classification exists only for governance completeness. | Architecture |

## Maintenance

**Every new hook added to `hooks/hooks.json` MUST receive a row in the table above before the PR merges.** This is a hard process requirement, not advisory.

**Audit-writing hooks** (any hook that appends to `$CLAUDE_PLUGIN_DATA/audit/`) MUST be classified `data_sensitivity: content` or higher. A hook classified `metadata` that silently writes content fields is a governance violation.

**`secret-risk` classification** requires a `sunset date:` entry in the notes column documenting when the capability will be removed or replaced. Open-ended `secret-risk` retention is not permitted.

Future work: a CI primitive that counts `hooks.json` entries and compares against rows in this table to detect governance drift (Scenario B follow-up; tracked but out of scope for PR #126).
