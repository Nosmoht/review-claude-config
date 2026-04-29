---
name: classify-trace-errors
description: >
  Classifies errors in a Claude Code audit trace or transcript JSONL against
  the MAST failure taxonomy. Outputs a structured error classification report
  with severity, evidence, and remediation guidance. Use when asked to
  'classify errors', 'analyze failures', or 'categorize trace errors'.
  Do NOT use for full session-trace review or behavioral-pattern analysis —
  use /review-session-trace instead.
argument-hint: <path-to-trace.jsonl>
allowed-tools: Read, Write, Glob, Grep
---

# Classify Trace Errors

You are an error classification tool that reads Claude Code audit traces or transcripts and maps observed patterns to the MAST failure taxonomy. Your job is to produce a structured report that categorizes runtime failures by type and severity.

## Argument Handling

- `$ARGUMENTS` is a path to a `.jsonl` file (audit trace or raw transcript).
- If empty, check `$CLAUDE_PLUGIN_DATA/audit/` for recent audit traces. If none found, ask the user for a path and stop.
- Validate the file exists and contains parseable JSONL.

## Termination and Escalation

**Termination conditions:**
- Grep returns >1000 matches for any pattern — cap at 500, note truncation
- >8 sequential tool calls without output — emit partial report and stop

**Escalation triggers (ask user):**
- File does not contain tool_use entries — may not be a session trace
- >20 distinct failure codes detected — session may need manual triage

## Phase 1 — Load References

### Step 1: Load Taxonomy

Read `references/failure-taxonomy.md` for the codebook (MAST failure modes, detection heuristics, severity levels).

### Step 2: Detect Trace Format

Read the first 10 lines. Determine format:
- **Audit trace** — entries have `"type": "tool_call"` (produced by observation hooks)
- **Raw transcript** — entries have `"message"` with `"content"` blocks (native Claude Code JSONL)

Set format flag for parsing logic below.

## Phase 2 — Pattern Detection (Steps 3-8 are parallelizable — run all Grep calls together)

**Resource caps:** Read ≤100 lines directly, use Grep for bulk extraction.

### Step 3: Detect FM-1.3 (Step Repetition)

Grep for all tool_use entries. Identify sequences where the same tool_name + input appears ≥3 times consecutively. For audit traces: same `tool_name` + `input_hash`. For transcripts: same `"name"` field in consecutive `tool_use` blocks.

### Step 4: Detect FM-1.5 (Unaware of Termination)

Count total tool calls. If >200 with no session_summary or stop signal, flag.

### Step 5: Detect FM-2.6 (Reasoning-Action Mismatch)

For raw transcripts only: Grep for `"type": "thinking"` entries. For each, check if the next `tool_use` block's tool name appears in the thinking text. Flag mismatches for the first 5 instances found.

### Step 6: Detect FM-3.1 (Premature Termination)

Check last 20 lines. If the final assistant entry contains a `tool_use` block with no matching `tool_result` in subsequent entries, flag.

### Step 7: Detect FM-3.2 (No Verification)

Grep for Write/Edit tool calls. For each, check whether a Read or Grep call targeting the same path appears within the next 10 entries. Flag unverified writes.

### Step 8: Detect FM-1.4 (Context Loss)

Grep for compaction signals (`"compact"` or `"type": "system"`). If found, check subsequent 10 entries for tool patterns that duplicate earlier patterns.

**Error handling:** If Grep returns 0 for any pattern, record that failure mode as "not detected" (count: 0). If Grep fails, skip that detection and note in report.

Step 9 requires output from Steps 3-8.

### Step 9: Aggregate and Classify

For each detected pattern, produce a classification entry per the schema in the taxonomy codebook. Sort by severity (High → Medium → Low), then by count.

Compute summary:
- Total failure modes detected
- High/Medium/Low counts
- Dominant failure category (FC1/FC2/FC3)

## Phase 3 — Output

### Status
[clean | caution | concern]
- `clean` — 0 failures detected
- `caution` — only Low/Medium failures
- `concern` — any High failure

### Classification Summary

| Category | Failures | Dominant Mode |
|---|---|---|
| FC1 — Specification | [N] | [FM-X.Y] |
| FC2 — Misalignment | [N] | [FM-X.Y] |
| FC3 — Verification | [N] | [FM-X.Y] |
| **Total** | **[N]** | |

### Detected Failures

[For each failure, ordered by severity:]

#### FM-X.Y: [Name] (Severity: [H/M/L], Count: [N])
**Evidence:** Line [N]: `[excerpt]`
**Remediation:** [Specific fix recommendation]

[If no failures: "No failure modes detected in this trace."]

### Recommendations

[1-3 actionable recommendations targeting the dominant failure category.]

## Phase 4 — Report Persistence

1. Present the report.
2. Resolve `<repo-slug>` per `repo-identification.md` (Glob `**/review-claude-config/references/repo-identification.md`).
3. Confirm before writing to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-classify-trace-errors.md`.
4. Frontmatter:
   ```yaml
   ---
   generated_by: classify-trace-errors
   schema_version: 1
   date: YYYY-MM-DD
   repo: <slug>
   origin: <git-remote-url>    # Optional
   target: /path/to/trace.jsonl
   summary:
     - name: trace-classification
       type: TraceClassification
       path: relative/path/to/trace.jsonl
       status: clean|caution|concern
       total_failures: N
       high: N
       medium: N
       low: N
   ---
   ```

## Hard Rules

- **Read-only on the trace.** Never modify the analyzed file. Write only to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/`.
- **Tier A justification:** Write is for report persistence only. No web tools needed.
- **Evidence over inference.** Every classification must cite a line number and excerpt. Do not classify based on absence alone except for FM-3.1 and FM-3.2.
- **Taxonomy-only codes.** Only use FM-* codes from the codebook. Do not invent new failure modes.
- **Present the full report before any follow-up actions.**
