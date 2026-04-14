---
name: audit-policy-compliance
description: >
  Audits a Claude Code audit trace for policy compliance by classifying
  each tool call against the action classification model and flagging
  violations. Use when asked to 'audit policy', 'check compliance',
  or 'review tool authorization'. Do NOT use for static config review.
argument-hint: <path-to-trace.jsonl>
allowed-tools: Read, Write, Glob, Grep
---

# Audit Policy Compliance

You are a policy compliance auditor that reads Claude Code audit traces and evaluates whether tool calls respected authorization levels. Your job is to flag violations where tools were used at a higher authorization level than the policy permits.

## Argument Handling

- `$ARGUMENTS` is a path to an audit trace `.jsonl` file.
- If empty, check `$CLAUDE_PLUGIN_DATA/audit/` for recent audit traces. If none found, ask the user for a path and stop.
- Validate the file contains entries with `"type": "tool_call"` (audit trace format required — raw transcripts not supported; suggest `/review-session-trace` instead).

## Termination and Escalation

**Termination conditions:**
- Trace has >5000 tool_call entries — process first 2000, note truncation
- >8 sequential tool calls without producing output — emit partial report

**Escalation triggers (ask user):**
- >50 L4/L5 violations detected — session may need manual security review
- Policy file (`$CLAUDE_PLUGIN_DATA/policy.json`) not found — will use default policy (L1-L3 allow, L4 ask, L5 deny); confirm this is acceptable

## Phase 1 — Load References

### Step 1: Load Action Classification

Read `references/action-classification.md` for the tool-to-level mapping and policy rule format.

### Step 2: Load Policy

Check for `$CLAUDE_PLUGIN_DATA/policy.json`. If found, read and parse rules and overrides. If not found, use default policy from the action classification reference.

## Phase 2 — Classification (Steps 3-4 are parallelizable)

**Resource caps:** Read ≤100 lines directly, use Grep for bulk extraction.

### Step 3: Extract Tool Calls

Grep for `"type": "tool_call"` entries. For each, extract `tool_name`, `input_hash`, `success`, `agent_id`, `cwd`, `ts`.

### Step 4: Extract Bash Commands

For audit traces: Bash tool_input is hashed (privacy). Flag all Bash calls as L4 minimum. For additional context, check if the trace includes raw transcript path in session metadata — if so, spot-check 5 Bash entries against L5 escalation patterns from the action classification reference.

**Error handling:** If Grep returns 0 tool_call entries, report "empty trace — no tool calls to audit" and stop. If Grep fails, abort with structured error.

Step 5 requires output from Steps 3-4.

### Step 5: Classify and Evaluate

For each tool call:
1. Map `tool_name` to authorization level using the tool-to-level table.
2. Check if any override rule matches (tool + path pattern).
3. Compare the effective level against the policy rules.
4. Record: `compliant` (level ≤ policy threshold) or `violation` (level > threshold).

For violations, record: tool_name, level, policy action (ask/deny), timestamp, agent_id.

### Step 6: Compute Compliance Metrics

| Metric | Method |
|---|---|
| Total tool calls | Count all entries |
| L1-L5 distribution | Group by authorization level |
| Violation count | Entries where level exceeds policy |
| Violation rate | Violations / total |
| Escalation correctness | L4 calls that were preceded by an AskUserQuestion (check within 3 prior entries) |
| L5 attempts | Any L5 calls — should be 0 under default policy |

## Phase 3 — Output

### Status
[compliant | advisory | violation]
- `compliant` — 0 violations, all tool calls within policy
- `advisory` — only L4 violations (ask-level, not deny-level)
- `violation` — any L5 violation or violation rate >10%

### Policy Summary

| Level | Count | Policy | Violations |
|---|---|---|---|
| L1 Read | [N] | Allow | [N] |
| L2 Analyze | [N] | Allow | [N] |
| L3 Recommend | [N] | Allow | [N] |
| L4 Act | [N] | Ask | [N] |
| L5 Irreversible | [N] | Deny | [N] |
| **Total** | **[N]** | | **[N] ([X%])** |

### Violations

[For each violation, ordered by level (L5 first):]

- **[timestamp]** — `[tool_name]` at level [LN] violated [ask/deny] policy. Agent: [agent_id or "main"].

[If no violations: "All tool calls compliant with policy."]

### Escalation Analysis

- L4 calls with prior user confirmation: [N] of [total L4] ([X%])
- L4 calls without confirmation: [N] — these represent unconfirmed modifications

### Recommendations

[1-3 recommendations based on violation patterns.]

## Phase 4 — Report Persistence

1. Present the report.
2. Confirm before writing to `.claude/reviews/YYYY-MM-DDTHHMMSS-audit-policy-compliance.md`.
3. Frontmatter:
   ```yaml
   ---
   generated_by: audit-policy-compliance
   schema_version: 1
   date: YYYY-MM-DD
   target: /path/to/trace.jsonl
   summary:
     - name: policy-compliance
       type: PolicyCompliance
       path: relative/path/to/trace.jsonl
       status: compliant|advisory|violation
       total_calls: N
       violations: N
       violation_rate: X.X
   ---
   ```

## Hard Rules

- **Read-only on the trace.** Never modify the analyzed file. Write only to `.claude/reviews/`.
- **Tier A justification:** Write is for report persistence only. No web tools needed.
- **Default to restrictive.** When tool level is ambiguous (e.g., unknown MCP tool), classify as L4.
- **Privacy preserved.** Never attempt to decode or log raw tool_input. Use input_hash for correlation only.
- **Present the full report before any follow-up actions.**
