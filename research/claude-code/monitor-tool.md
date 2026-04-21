---
last_refreshed: 2026-04-19
---

# Claude Code Monitor Tool

Reference for the Monitor tool (Claude Code v2.1.98+). Streams stdout from a background process as per-line events, enabling real-time reaction during a session. Contrast with `Bash(run_in_background:true)` (one-shot, notification on completion) and `/loop` (fixed-interval recurrence).

## TL;DR

- Monitor starts a background script and streams each stdout line as an event — Claude reacts **during** execution, not after.
- Permissions inherit the Bash tool's allow/deny patterns.
- Plugins can auto-start monitors via a `monitors` manifest key.
- NOT available on Bedrock/Vertex/Foundry or when telemetry is disabled.
- Two known bugs active as of 2026-04-19: #50258 (notification flooding in poll loops), #45976 (tmux session detachment).

## Execution Model

| Aspect | Detail |
|--------|--------|
| Invocation | Claude writes a script, starts it in background, receives lines streamed back |
| Session context | Runs in the same session — conversation state persists |
| Permissions | Inherits Bash tool deny patterns (allow/deny rules work identically) |
| Event granularity | Each stdout line is one event; multiline bursts within ~200 ms are batched |
| Control | `TaskStop <id>` kills a monitor; Esc cancels pending wakeups; session-end stops all |

## Plugin Integration

A plugin may declare monitors in its manifest:

```json
{
  "monitors": {
    "tail-errors": { "command": "tail -F /var/log/app.log | grep ERROR" }
  }
}
```

Monitors listed this way auto-start when the plugin is active. (Manifest key is mentioned in docs but lacks code examples as of 2026-04-19 — see issue #47619.)

## Comparison to Alternatives

| Aspect | `Bash(run_in_background)` | Monitor | `/loop` |
|--------|---------------------------|---------|---------|
| Timing | One-shot, notification on completion | Streaming events during execution | Recurring at interval |
| Reaction | After the task ends | Immediate, during execution | After each interval |
| Use case | Long-running jobs without interaction | Real-time log tailing, poll loops | Scheduled maintenance, polling with cadence control |
| Cache-aware | No | Streaming requires each event to be re-processed — breaks prompt-cache fast-path | Yes — sub-300s intervals stay cache-warm |

## Known Issues (open as of 2026-04-19)

| Issue | Status | Impact | Priority |
|-------|--------|--------|----------|
| #50258 Notification flooding in poll loops | Open (2026-04-18) | UX spam | Medium |
| #45976 Monitor events detach tmux sessions | Open (2026-04-10) | Stability / crash | High |
| #47518 Missing visibility in scheduled wakeups | Open (2026-04-13) | Observability gap | Medium |
| #47619 Docs missing `monitors` manifest key examples | Open (2026-04-13) | Documentation | Low |

## Availability Gaps

| Environment | Support |
|-------------|---------|
| Anthropic direct | ✓ |
| Amazon Bedrock | ✗ |
| Google Vertex AI | ✗ |
| Microsoft Foundry | ✗ |
| `DISABLE_TELEMETRY=1` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` | ✗ |

## Implications for Review Plugin

- Not a new reviewable primitive — Monitor is operational infrastructure.
- Potential operational benefit: long-running skills (`run-eval-cases`, `refresh-baseline`) could surface progress events live instead of blocking until completion.
- Tmux-detach bug (#45976) makes Monitor risky in sessions where the user runs Claude Code inside tmux. Defer adoption until fix lands.
- Internal review plugin roadmap: defer to P3 until #50258 and #45976 are resolved upstream.

## Open Questions

- Can Monitor poll remote APIs (REST/GraphQL) or only local scripts/commands?
- What is the maximum line length the event stream handles without truncation?
- Are Bash `allow(rm:*)` deny patterns applied 1:1 to Monitor-spawned shells, or does it get its own matcher set?

## Sources

Tier 1:
- [Claude Code — Tools Reference](https://code.claude.com/docs/en/tools) — Monitor section, accessed 2026-04-19
- [claude-code issues](https://github.com/anthropics/claude-code/issues) — #50258, #45976, #47518, #47619 accessed 2026-04-19

Tier 2:
- [Monitor Tool guide (claudefa.st)](https://claudefa.st/blog/guide/mechanics/monitor) — 2026-04-09
