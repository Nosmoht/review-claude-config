---
last_refreshed: 2026-04-14
---

# Hook-Based Runtime Observation Patterns for Claude Code

## Provenance Metadata

- Strongest source tier: Tier 1
- Source basis: Anthropic official documentation (code.claude.com hooks reference and hooks guide) + verified production hook implementations in this repository + Tier 2 production bug reports from anthropics/claude-code
- Last reviewed: 2026-04-14

**Sources:**
- [Hooks reference — Claude Code Docs](https://code.claude.com/docs/en/hooks) (Tier 1 — Anthropic official)
- [Hooks guide — Claude Code Docs](https://code.claude.com/docs/en/hooks-guide) (Tier 1 — Anthropic official)
- [BUG: PreToolUse hooks exit code ignored — anthropics/claude-code #21988](https://github.com/anthropics/claude-code/issues/21988) (Tier 2 — confirmed production bug)
- [Multi-Primitive Dependency Integrity](../multi-primitive-dependencies/multi-primitive-dependency-integrity.md) (Repo internal — verified exit-code contract analysis)
- [Autonomous Agent Reliability](../autonomous-agent-reliability/autonomous-agent-reliability.md) (Repo internal — R10 observability requirement)

## Key Finding

Claude Code hooks provide **per-event, discrete observation points** across 26+ lifecycle events — sufficient for structured audit logging but not continuous monitoring. The richest observation data comes from tool events (PreToolUse/PostToolUse), which expose `tool_name`, `tool_input`, and `tool_use_id`. All events share common fields (`session_id`, `transcript_path`, `cwd`, `agent_id`, `agent_type`) enabling session-level correlation. The `transcript_path` field — pointing to the full JSONL conversation record — is the most underutilized observation asset: it provides comprehensive post-hoc analysis without hook overhead. The primary architectural limit is that hooks observe **actions**, not **reasoning** — token counts, cost data, model confidence, and cache state are invisible.

---

## Evidence

### Hook Event Taxonomy for Observation

Claude Code fires hooks at three cadences. Observation value is rated by what runtime-audit-relevant data is accessible.

**Source:** [Hooks reference](https://code.claude.com/docs/en/hooks) (Tier 1)

#### Per-Session Events (session lifecycle)

| Event | Fires When | Observation Value | Key Data |
|---|---|---|---|
| SessionStart | Session begins/resumes | **High** — inject audit context, initialize log | `source` (startup/resume/clear/compact), common fields |
| SessionEnd | Session terminates | **High** — finalize audit record, aggregate metrics | `source` (clear/resume/logout/exit/other), common fields |

#### Per-Turn Events (user-agent interaction boundary)

| Event | Fires When | Observation Value | Key Data |
|---|---|---|---|
| UserPromptSubmit | User sends prompt, before processing | **Medium** — log user intent, detect scope | `prompt` (full user text) |
| Stop | Claude finishes responding | **Medium** — session-end aggregation point | `stop_hook_active` (loop guard) |
| StopFailure | Turn ends due to API error | **High** — error rate tracking | `error_type` (rate_limit, auth_failed, billing, server_error, max_output_tokens) |

#### Per-Tool-Call Events (highest observation density)

| Event | Fires When | Observation Value | Key Data |
|---|---|---|---|
| PreToolUse | Before tool execution | **Critical** — audit gate + pre-action log | `tool_name`, `tool_input` (full args), `tool_use_id` |
| PostToolUse | After successful execution | **Critical** — outcome logging | `tool_name`, `tool_input`, `tool_use_id`, tool output |
| PostToolUseFailure | After tool failure | **Critical** — error classification | `tool_name`, `tool_input`, `tool_use_id`, error data |
| PermissionRequest | Permission dialog appears | **Medium** — escalation tracking | `tool_name`, `tool_input` |
| PermissionDenied | Auto-mode denies tool | **High** — policy violation log | `tool_name`, `tool_input` |

#### Agentic Loop Events (delegation chain visibility)

| Event | Fires When | Observation Value | Key Data |
|---|---|---|---|
| SubagentStart | Subagent spawned | **High** — delegation tree, depth tracking | Matcher on agent type (Bash/Explore/Plan/custom) |
| SubagentStop | Subagent completes | **High** — delegation outcome, duration | Same matcher |
| TaskCreated | Task created via TaskCreate | **Medium** — workflow progress | Task metadata |
| TaskCompleted | Task marked completed | **Medium** — completion tracking | Task metadata |
| TeammateIdle | Team member about to idle | **Low** — team utilization | Agent context |

#### Configuration and File Events

| Event | Fires When | Observation Value | Key Data |
|---|---|---|---|
| FileChanged | Watched file changes on disk | **Medium** — side-effect detection | `file_path`, `watch_paths` |
| ConfigChange | Settings change mid-session | **High** — config drift detection | `source` (user/project/local/policy/skills), `file_path` |
| InstructionsLoaded | CLAUDE.md/rules loaded | **Low** — context assembly audit | Load reason (session_start/traversal/glob/include/compact) |
| CwdChanged | Working directory changes | **Low** — scope tracking | New cwd in common fields |
| PreCompact / PostCompact | Context compaction | **Medium** — context lifecycle | Trigger (manual/auto) |

#### Additional Events (low observation value for audit)

| Event | Fires When | Observation Value | Key Data |
|---|---|---|---|
| Notification | Agent sends notification | **Low** — notification audit | Type (permission_prompt/idle_prompt/auth_success/elicitation_dialog) |
| Elicitation / ElicitationResult | MCP server requests user input / user responds | **Medium** — MCP interaction audit | `mcp_server_name`, elicitation input/response |
| WorktreeCreate / WorktreeRemove | Git worktree lifecycle | **Low** — isolation tracking | Worktree path |

---

### Common Input Fields (All Events)

Every hook receives these fields on stdin, enabling session-level correlation. These fields are documented in the [official hooks reference](https://code.claude.com/docs/en/hooks) (Tier 1) but are not yet used by any hook implementation in this repo — existing hooks (`skill_quality_gate.py`, `session_check.py`) only parse `tool_input` and environment variables respectively.

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "agent_id": "agent-123",
  "agent_type": "Explore"
}
```

**Source:** [Hooks reference](https://code.claude.com/docs/en/hooks) (Tier 1)

**Key observation assets:**
- `session_id` — correlate all events within one session
- `transcript_path` — full conversation JSONL for post-hoc analysis without per-event overhead
- `agent_id` + `agent_type` — reconstruct delegation chains; detect which events occur in subagent context
- `cwd` — detect working directory drift during session

---

### Observation Patterns

#### Pattern 1: PostToolUse Audit Logger (non-blocking, per-call)

Append a structured JSONL line for every tool call. Use `async: true` to avoid blocking the agent.

**Configuration:**
```json
{
  "PostToolUse": [{
    "hooks": [{
      "type": "command",
      "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/audit_logger.py",
      "async": true
    }]
  }]
}
```

**Observable fields:** `tool_name`, `tool_input` (hash for privacy — see Operational Considerations), `tool_use_id`, `session_id`, `agent_id`, timestamp (hook-generated), success (inferred from PostToolUse vs PostToolUseFailure).

**What it cannot observe:** Tool execution duration (no start timestamp in PostToolUse — must pair with PreToolUse), token consumption, cost.

**Limitation:** Async hooks run in the background — if the hook fails, no data is written and no error surfaces unless `asyncRewake: true` is set.

#### Pattern 2: PreToolUse Policy Gate (blocking, per-call)

Deterministic pre-action authorization that also logs the decision. Synchronous — must complete within timeout.

**Decision output:** `permissionDecision` of `allow`, `deny`, or `ask` with `permissionDecisionReason` providing the audit trail.

**Key constraint:** PreToolUse `allow` does NOT override deny rules from settings. A hook cannot grant more permissions than the user's settings allow.

**Performance requirement:** PreToolUse hooks block the agent — latency directly impacts responsiveness. Keep under 100ms for interactive use.

#### Pattern 3: Session Bookend Summary (SessionStart + Stop/SessionEnd)

SessionStart initializes the audit record. Stop or SessionEnd writes the session summary.

**SessionStart output:** `additionalContext` injects audit orientation into the agent's context (e.g., "This session is being audited — all tool calls are logged").

**Stop/SessionEnd output:** Read the accumulated audit log, compute summary metrics, write final report.

**Caveat:** Stop fires every time Claude yields for input, not only at task completion. Use SessionEnd for true session termination.

#### Pattern 4: Delegation Chain Tracker (SubagentStart/SubagentStop)

Log subagent spawn/completion events to reconstruct the delegation tree.

**Configuration:**
```json
{
  "SubagentStart": [{ "hooks": [{
    "type": "command",
    "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/delegation_tracker.py",
    "async": true
  }]}],
  "SubagentStop": [{ "hooks": [{
    "type": "command",
    "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/delegation_tracker.py",
    "async": true
  }]}]
}
```

**Observable:** `agent_type` (from matcher), `agent_id` + parent `agent_id` (from common fields), `hook_event_name` (SubagentStart vs SubagentStop), timestamp (hook-generated).

**Correlation:** Each SubagentStart includes the spawning context's `agent_id`. The matching SubagentStop carries the same `agent_id`. To reconstruct the tree: store `{agent_id, parent_agent_id, agent_type, start_time}` on SubagentStart; update with `{end_time, duration}` on SubagentStop. Max depth = longest chain of parent_agent_id links.

**Key use:** Detect delegation depth violations, circular delegation patterns, and subagent failure propagation.

#### Pattern 5: Stateful Observation via CLAUDE_ENV_FILE

SessionStart and CwdChanged hooks can persist state to `$CLAUDE_ENV_FILE`. Subsequent Bash commands inherit these variables. This enables session-scoped counters (tool call count, error count) without external storage.

**Limitation:** Only available to SessionStart, CwdChanged, and FileChanged hooks — not to tool event hooks.

**Source:** [Hooks guide](https://code.claude.com/docs/en/hooks-guide) (Tier 1)

---

### Signal Aggregation: Session-Level Metrics from Hook Data

By combining per-event data, hooks can produce session-level audit signals:

| Metric | Source Events | Aggregation |
|---|---|---|
| Tool call count by type | PostToolUse | Count group by `tool_name` |
| Error rate | PostToolUseFailure / (PostToolUse + PostToolUseFailure) | Ratio per tool |
| Retry count | PreToolUse with same `tool_name` + similar `tool_input` in sequence | Heuristic: consecutive same-tool calls |
| Delegation depth | SubagentStart/SubagentStop | Max nesting of `agent_id` chains |
| Permission escalation rate | PermissionRequest count / total tool calls | Ratio |
| Policy violation count | PermissionDenied events | Count |
| Session duration | SessionStart timestamp to SessionEnd timestamp | Delta |
| Context compaction events | PreCompact/PostCompact | Count, distinguishing manual vs auto |
| Config drift | ConfigChange events | Count + source classification |

**What CANNOT be aggregated from hooks:**
- Token consumption (not exposed to hooks)
- Cost per session or per tool call (not exposed)
- Model confidence or uncertainty (not exposed)
- Cache hit/miss rate (not exposed)
- Context window fill percentage (not exposed)

---

### Operational Considerations for Observation Hooks

#### Observer Failure and Data Loss

Observation hooks use the mandatory safety wrapper (`try/except/finally: sys.exit(0)`) from the develop-hooks skill. This guarantees the agent is never blocked by a failing observer — but the tradeoff is **silent data loss**: a disk-full error, permission error, or unhandled exception means the audit log entry is simply not written. No error surfaces to the user or the agent.

**Mitigation:** Use `asyncRewake: true` for critical audit hooks — if the hook exits 2, Claude is woken and receives stderr as feedback, enabling alerting on observer failure. For non-critical logging, accept the silent-loss tradeoff.

#### Privacy and Data Sensitivity

`tool_input` fields may contain file contents (Write), shell commands with credentials (Bash), or user data (MCP tools). An audit logger that writes raw `tool_input` to disk creates a secondary exposure surface.

**Mitigation:** Log `tool_name` and a hash of `tool_input` (e.g., SHA-256 of JSON-serialized input) for correlation. Write full `tool_input` only behind an explicit opt-in flag and to an access-controlled location. Never log `tool_input` for Bash commands matching credential patterns (`*token*`, `*secret*`, `*password*`).

#### Log Rotation and Storage

Pattern 1 writes unbounded JSONL. A session with 500+ tool calls produces significant log volume. No built-in rotation exists.

**Mitigation:** SessionEnd hook should check log size and archive/rotate. Set a per-session size cap (e.g., 10MB). Alternatively, write to a dedicated `$CLAUDE_PLUGIN_DATA/audit/` directory with date-based filenames and prune sessions older than a retention period.

#### Testing Observation Hooks

Async hooks are difficult to test in live sessions because failures are silent. The develop-hooks skill provides a `echo '{}' | python3 hook.py` smoke test pattern, but this does not validate async behavior.

**Recommended approach:** (1) Unit test the Python script with synthetic stdin JSON (as existing repo tests do for `skill_quality_gate.py` and `session_check.py`). (2) Verify log file existence after a manual session that triggers the hook. (3) For critical observers, add a heartbeat check in the SessionEnd hook that verifies the expected number of log entries approximates the tool call count.

---

### Execution Model Constraints

**Source:** [Hooks reference](https://code.claude.com/docs/en/hooks) (Tier 1)

| Constraint | Value | Implication for Observation |
|---|---|---|
| Multiple hooks on same event | Run in **parallel** | Log entries may arrive out of order; use `tool_use_id` for correlation |
| Decision composition | Most restrictive wins (`deny` > `ask` > `allow`) | Observation hooks should use `async: true` to avoid accidental blocking |
| Default timeout | 600s (command), 30s (prompt), 60s (agent) | Observation hooks should set explicit short timeouts (5-10s) |
| Exit code 2 | Blocking error — stops the action | Observation hooks must NEVER exit 2; always exit 0 |
| Exit code 1 | Non-blocking error — action proceeds | Safe for observation but generates transcript noise |
| Async hooks | `async: true` — run in background | Best for audit logging; no blocking, no latency cost |
| `asyncRewake: true` | Background hook exit 2 wakes Claude | Enables deferred alerting for anomaly detection |

**Exit code discrepancy (resolved 2026-04-14):** The hook-evaluation-guide PY-3 previously stated "0=pass, 1=block, 2=non-blocking" — inverted relative to the [official hooks reference](https://code.claude.com/docs/en/hooks) and the [multi-primitive-dependencies exit-code analysis](../multi-primitive-dependencies/multi-primitive-dependency-integrity.md). The correct semantics are: **exit 0 = pass, exit 2 = block, exit 1/other = non-blocking error**. PY-3 and SR-4 have been corrected in this commit.

**Critical safety rule for observation hooks:** Always exit 0. Never use exit code 2. An observation hook that accidentally blocks tool execution converts a monitoring system into a control system — violating separation of concerns and creating cascading failure risk.

**Source:** [Multi-Primitive Dependency Integrity](../multi-primitive-dependencies/multi-primitive-dependency-integrity.md) (exit-code contract analysis)

---

### The Transcript Path: Underutilized Observation Asset

Every hook receives `transcript_path` — the path to the session's full JSONL conversation record. This file contains:
- All user prompts
- All Claude responses
- All tool calls with inputs and outputs
- All permission decisions
- Timestamps for every event

**Post-hoc analysis via transcript is strictly more powerful than per-event hooks** because it captures the full conversation context, not just tool events. A `/review-session-trace` skill that reads this file can extract any metric that hooks can observe, plus conversation flow, reasoning patterns, and context evolution — without requiring any hook infrastructure at all.

**Trade-off:** Transcript analysis is post-hoc only — it cannot block or modify actions in real-time. Hooks are needed for pre-action gates (Pattern 2). For pure observation, the transcript is superior.

---

### Architectural Boundaries

| What Hooks CAN Observe | What Hooks CANNOT Observe |
|---|---|
| Tool names, inputs, and outputs | Token counts (input/output/cache) |
| Session lifecycle events | Cost data (pricing, aggregate spend) |
| Delegation chains (subagent start/stop) | Model confidence or uncertainty |
| Permission decisions and escalations | Cache hit/miss status |
| Configuration changes mid-session | Context window fill percentage |
| File changes on disk | Reasoning traces (thinking blocks) |
| User prompts before processing | Model attention or embedding state |
| Working directory changes | Latency per API call (no timing data in hook input) |

**Implication:** A hook-based observation system can answer "what did the agent do?" but not "how much did it cost?" or "how confident was it?" Cost and token tracking require an **API proxy** between Claude Code and the Anthropic API. Confidence requires **model-level instrumentation** not available in the current architecture.

---

## Implications for Audit Harness Roadmap

1. **Phase 1 (Trace Layer) is feasible with hooks alone.** PostToolUse async loggers + SubagentStart/Stop trackers + SessionStart/End bookends provide sufficient data for structured audit trails. No external infrastructure needed.

2. **The transcript file is the fastest path to runtime analysis.** A `/review-session-trace` skill (QW-4) that reads `transcript_path` JSONL provides immediate value with zero hook infrastructure — it's a read-only skill operating on an existing artifact.

3. **Pre-action authorization (Phase 2b) is feasible via PreToolUse hooks.** The `permissionDecision` mechanism directly implements the policy gate pattern. Multiple hooks compose with deny-wins semantics, enabling layered security.

4. **Cost and token tracking (§1.15) require external infrastructure.** Hooks cannot observe these — an API proxy or billing integration is the only path.

5. **Kill switches and containment (§2.6) are partially feasible.** PreToolUse can deny individual tool calls but cannot terminate a session. Full containment requires an external process manager.

6. **Observation hooks must be async to preserve agent performance.** Synchronous observation hooks on every tool call would measurably degrade interactive responsiveness. Use `async: true` for all logging hooks; reserve synchronous execution for policy gates only.

7. **Exit code discipline is critical.** Per the exit-code contract analysis in multi-primitive-dependencies research, observation hooks must always exit 0. Exit 2 blocks actions; exit 1 creates transcript noise. The safety wrapper pattern (`try/except/finally: sys.exit(0)`) is mandatory.
