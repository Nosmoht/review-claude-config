---
name: review-session-trace
description: >
  Analyzes a Claude Code JSONL transcript and produces a structured trace
  report: tool-call distribution, error rates, retry patterns, delegation
  chains, token usage, and behavioral signals mapped to MAST failure modes.
  Use when asked to 'review trace', 'analyze session', or 'audit transcript'.
  Do NOT use for narrow error classification against MAST taxonomy —
  use /classify-trace-errors instead.
argument-hint: <path-to-transcript.jsonl>
allowed-tools: Read, Write, Glob, Grep
---

# Review Session Trace

You are a trace analysis tool that reads Claude Code JSONL transcripts and produces structured runtime audit reports. Your job is to extract quantitative signals from session data and flag behavioral patterns that indicate reliability risks.

## Argument Handling

- `$ARGUMENTS` is the path to a `.jsonl` transcript file.
- If empty, check `~/.claude/projects/` for recent transcripts and suggest the most recent one. If no transcripts found, ask the user for a path and stop.
- Validate the file exists and the first line parses as JSON with a `uuid` field.
- If the file is not a valid transcript, report the error and stop.

## Termination and Escalation

**Termination conditions (abort with partial report if any is met):**
- Grep returns >1000 matches for any single pattern — cap processing at 500, note truncation in report
- Analysis exceeds 8 sequential tool calls without producing output — emit partial report and stop
- File size >50 MB — report "transcript too large for skill-based analysis" and stop

**Escalation triggers (ask the user before continuing):**
- Transcript first line does not parse as JSON — may be wrong file format
- >10 behavioral patterns detected — session may warrant manual inspection
- Grep returns 0 tool_use matches — transcript may be empty or a non-standard format

## Phase 1 — Parsing

### Step 0: Tool Availability

Verify Grep works by running a trivial pattern on the transcript (e.g., `"uuid"`). If Grep fails, report error and stop — this skill requires Grep for bulk extraction.

### Step 1: Load Schema

Read `references/transcript-schema.md` for the JSONL entry structure.

Also load `repo-identification.md` via Glob `**/review-claude-config/references/repo-identification.md` to resolve `suite-root` and `repo-slug`.

### Step 2: Sample the Transcript

Read the first 50 lines and the last 20 lines to determine session boundaries (start/end timestamps, session ID, total line count via Grep for line count).

### Steps 3-5: Bulk Extraction (parallelizable — run all Grep calls together)

**Step 3 — Tool calls:** Grep for `"type":\s*"tool_use"` to extract tool names and IDs. Grep for `"type":\s*"tool_result"` to count results and detect failures (content containing `"error"` or `"Error"`).

**Step 4 — Token usage:** Grep for `"input_tokens"` to find usage objects. Sum `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`.

**Step 5 — Delegation:** Grep for `"name":\s*"Agent"` in tool_use blocks to identify subagent spawns. Count delegation depth from nested agent calls.

**Resource caps (hard limits per analysis):** Read ≤200 lines directly (sampling), use Grep for bulk extraction. Do not read the entire transcript into context — transcripts can exceed 100K tokens.

**Error handling for each extraction step:**
- Grep returns 0 matches → record metric as 0, note "no data" in the corresponding output section
- Grep returns error → stop extraction for that metric, continue with remaining steps, note in report
- Read fails (file locked, permission denied) → abort with structured error block
- Truncated transcript (last line is incomplete JSON) → ignore last line, note "transcript appears truncated" in Session Summary

## Phase 2 — Analysis

Steps 6 and 7 require output from Steps 3-5. Step 8 requires output from Steps 6-7.

### Step 6: Compute Metrics

From the extracted data, compute:

| Metric | Method |
|---|---|
| Session duration | Last timestamp - first timestamp |
| Total turns | Count of `type: "assistant"` entries |
| Tool call count by tool | Group tool_use blocks by `name` |
| Tool error rate | tool_results with error content / total results |
| Retry signal | Consecutive tool_use blocks repeated 2 times or more with same `name` in same assistant turn |
| Delegation depth | Max nesting level of Agent tool_use blocks |
| Token totals | Sum of usage fields |
| Cache hit rate | cache_read / (cache_read + input_tokens) |

### Step 7: Behavioral Pattern Detection

Check for these patterns (mapped to MAST failure modes from `research/autonomous-agent-reliability/autonomous-agent-reliability.md`):

| Pattern | Detection Heuristic | MAST Mapping |
|---|---|---|
| Step repetition | Same tool+input called ≥3 times consecutively | FM-1.3 |
| Unbounded retry | Same tool called ≥5 times without different approach | FM-1.5 |
| Premature termination | Session ends with pending tool_use (no matching result) | FM-3.1 |
| No verification | Write/Edit tools used with no subsequent Read/Grep | FM-3.2 |
| Reasoning-action mismatch | Thinking block contains tool name A, next tool_use calls tool B (check first 3 thinking+tool_use pairs that have a tool name in thinking text) | FM-2.6 |
| Context loss signal | Entry with `"compact"` in content, followed within 5 turns by a user prompt substantially similar to one already asked (same tool+input pattern) | FM-1.4 |

Report each detected pattern with: count, example evidence (line number + content excerpt), severity (High/Medium/Low).

### Step 8: Risk Summary

Classify the session:
- **Clean** — 0 behavioral patterns detected, error rate <5%
- **Caution** — 1-2 Low/Medium patterns or error rate 5-15%
- **Concern** — any High pattern or error rate >15% or ≥3 patterns total

## Phase 3 — Output

Return the report in this exact format:

### Status
[clean | caution | concern]

### Session Summary

| Metric | Value |
|---|---|
| Transcript | [filename] |
| Duration | [X min Y sec] |
| Turns | [N] |
| Tool calls | [N] |
| Tool errors | [N] ([X%]) |
| Subagent spawns | [N] (max depth [D]) |

### Tool Call Distribution

| Tool | Count | Errors | Error Rate |
|---|---|---|---|
| [tool_name] | [N] | [N] | [X%] |
| ... | ... | ... | ... |

### Token Usage

| Metric | Value |
|---|---|
| Input tokens | [N] |
| Output tokens | [N] |
| Cache reads | [N] |
| Cache creates | [N] |
| Cache hit rate | [X%] |

### Behavioral Signals

[For each detected pattern:]
- **[Pattern name]** (MAST [FM-X.Y], Severity: [H/M/L]) — [count] occurrences. Example: line [N], [brief evidence excerpt].

[If no patterns: "No behavioral signals detected."]

### Recommendations

[1-3 actionable recommendations based on findings. Reference specific patterns and suggest concrete mitigations.]

## Phase 4 — Report Persistence

1. Present the report to the user.
2. Confirm before writing: "Save trace report to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/YYYY-MM-DDTHHMMSS-review-session-trace.md`?"
3. If confirmed, create the `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/` directory if it does not exist. Write with frontmatter:
   ```yaml
   ---
   generated_by: review-session-trace
   schema_version: 1
   date: YYYY-MM-DD
   repo: <slug>
   origin: <git-remote-url>  # optional
   target: /path/to/transcript.jsonl
   summary:
     - name: session-trace
       type: SessionTrace
       path: relative/path/to/transcript.jsonl
       status: clean|caution|concern
       tool_calls: N
       tool_errors: N
       behavioral_signals: N
   ---
   ```

## Hard Rules

- **Read-only on the transcript.** Never modify the analyzed file. Write only to `$CLAUDE_PLUGIN_DATA/reports/<repo-slug>/`.
- **Tier A justification:** Write is for report persistence only. Grep/Read are for transcript parsing. No web tools needed.
- **Context budget discipline.** Do not read the full transcript into context. Use Grep for bulk extraction, Read with offset/limit for sampling. Transcripts can be 100K+ tokens.
- **Evidence over inference.** Report only patterns with concrete line-number evidence. Do not speculate about intent.
- **Present the full report before any follow-up actions.**
