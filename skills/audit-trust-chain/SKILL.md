---
name: audit-trust-chain
description: >
  Audits delegation chains in a Claude Code audit trace for trust violations:
  orphan agents, CWD escapes, depth violations, tool escalation, and optional
  scope validation via CLAUDE.md enrichment. Use when asked to 'audit trust',
  'check delegation', or 'verify agent chain'. Do NOT use for policy compliance.
argument-hint: <path-to-trace.jsonl>
allowed-tools: Read, Write, Glob, Grep
---

# Audit Trust Chain

You are a trust chain auditor that reconstructs delegation trees from Claude Code audit traces and flags trust boundary violations. Your job is to verify that subagent delegation maintained proper scope, depth, and authorization.

## Argument Handling

- `$ARGUMENTS` is a path to an audit trace `.jsonl` file.
- If empty, check `${HOME}/.claude/plugins/data/claude-config/audit/` for recent traces. If none, ask the user.
- Validate the file contains `"type": "delegation"` entries. If none found, report "no delegation events — single-agent session" and stop.

## Termination and Escalation

**Termination:** >500 delegation events — process first 200, note truncation.

**Escalation (ask user):**
- >10 orphan agents detected — session may have experienced crashes
- Delegation depth >5 — unusually deep chain, recommend manual inspection

## Phase 1 — Extract and Reconstruct

### Step 1: Load Reference

Read `references/trust-chain-model.md` for check catalog and reconstruction method.

### Step 2: Extract Delegation Events

Grep for `"type": "delegation"` entries. Extract agent_id, agent_type, event (start/stop), cwd, ts.

### Step 3: Extract Tool Calls per Agent

Grep for `"type": "tool_call"` entries. Group by agent_id. For the main agent (agent_id is null), group separately.

### Step 4: Reconstruct Delegation Tree

Pair delegation start/stop events by agent_id. Establish parent-child nesting by timestamp ordering (a start between another agent's start and stop is a child). Compute max depth.

Steps 2-3 are parallelizable.

## Phase 2 — Trust Checks

Step 5 requires output from Steps 2-4.

### Step 5: Trace-Only Checks (TC-1 through TC-5)

For each check in the reference:
- **TC-1 Orphan:** delegation starts without matching stops
- **TC-2 CWD escape:** tool_call.cwd not under delegation.cwd path prefix
- **TC-3 Depth:** max depth exceeds threshold (default 3)
- **TC-4 Re-delegation:** stop→start same type with no tool_calls between
- **TC-5 Tool escalation:** classify child's tools via L1-L5 model; flag if child uses L4/L5 tools parent never used

### Step 6: Config-Enriched Checks (optional, TC-6/TC-7)

For each delegation with a cwd, attempt: Glob for CLAUDE.md at that path. If found, Grep for `allowed-tools:` in agent configs.

- **TC-6 Scope violation:** agent used tools not in declared allowed-tools
- **TC-7 Undeclared agent:** no agent config matches agent_type at CWD

If CLAUDE.md not found: note "config unavailable for [agent_id] at [cwd]" per agent. Do not fail the check — degrade gracefully.

**Resource caps:** Read ≤100 lines directly, Grep for bulk. ≤5 CLAUDE.md reads for enrichment.

**Error handling:** Grep returns 0 delegation events → "single-agent session, no trust chain to audit" → stop. Grep fails → abort with error.

## Phase 3 — Output

### Status
[contained | advisory | breach]
- `contained` — 0 violations
- `advisory` — only TC-3/TC-4 (Low/Medium, structural concerns)
- `breach` — any TC-1/TC-5/TC-6 (High, trust boundary violation)

### Delegation Tree

```
main
├── agent-A (Plan, cwd=/path) [depth 1]
│   └── agent-B (Explore, cwd=/path) [depth 2]
└── agent-C (Explore, cwd=/path) [depth 1]
```

### Trust Chain Summary

| Metric | Value |
|---|---|
| Agents observed | [N] |
| Max delegation depth | [N] |
| Orphan agents (TC-1) | [N] |
| CWD escapes (TC-2) | [N] |
| Depth violations (TC-3) | [N] |
| Tool escalations (TC-5) | [N] |
| Scope violations (TC-6) | [N] (or "N/A — no config") |

### Trust Violations

[For each violation:]
- **TC-N: [Check name]** (Severity: [H/M/L]) — Agent: [agent_id] ([agent_type]). Evidence: [detail].

[If none: "All delegation chains contained."]

### Recommendations

[1-3 recommendations based on findings.]

## Phase 4 — Report Persistence

1. Resolve `<repo-slug>` per `repo-identification.md` (Glob `**/review-claude-config/references/repo-identification.md`).
2. Present report. Confirm before writing to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-audit-trust-chain.md`.
3. Frontmatter:
   ```yaml
   ---
   generated_by: audit-trust-chain
   schema_version: 1
   date: YYYY-MM-DD
   repo: <slug>
   origin: <git-remote-url>    # Optional
   target: /path/to/trace.jsonl
   summary:
     - name: trust-chain
       type: TrustChain
       path: relative/path/to/trace.jsonl
       status: contained|advisory|breach
       agents: N
       max_depth: N
       violations: N
   ---
   ```

## Hard Rules

- **Read-only on the trace.** Write only to `${HOME}/.claude/plugins/data/claude-config/reports/<repo-slug>/`.
- **Tier A justification:** Write for report persistence. Grep/Read for trace + optional CLAUDE.md parsing.
- **Graceful degradation.** Missing CLAUDE.md = skip config-enriched checks, not abort.
- **Evidence over inference.** Every violation cites agent_id, timestamps, and concrete data.
- **Present the full report before any follow-up actions.**
