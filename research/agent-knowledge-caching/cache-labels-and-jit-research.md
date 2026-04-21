---
last_refreshed: 2026-04-19
---

# Cache-Status Labels and Runtime JIT Research

Aperant-inspired patterns for labelling cached knowledge, detecting stuck sub-tasks, and performing runtime just-in-time research with source-quality classification. Feeds P2.4 (cache labels), P2.6 (runtime JIT), and stuck-detection logic in long-running skills.

## TL;DR

- 4-state cache label: `CACHED` / `STALE` / `FAILED` / `RUNTIME_RESEARCH`. Explicit state machine with documented transitions.
- Stuck-task detection uses a **2-hour sliding window of attempt timestamps** to avoid inflating counts after crashes/restarts. Hard cap 50 attempts per sub-task (oldest-first eviction).
- Runtime JIT research: 2–3 web queries per domain, Tier-1/2/3 source classification, injected into agent context as ephemera (no disk persistence).
- Aperant's RDR (Recover-Debug-Resend) system: 6 priority levels from auto-continue to recreate-from-scratch.

## Cache-Status Labels

### Schema

```typescript
type CacheStatusLabel = "CACHED" | "STALE" | "FAILED" | "RUNTIME_RESEARCH";

interface WorkItemCacheStatus {
  label:           CacheStatusLabel;
  last_refreshed:  string;    // ISO 8601
  ttl_hours?:      number;
  reason?:         string;    // for FAILED or RUNTIME_RESEARCH
}
```

### State Transitions

```
CACHED
  ├── last_refreshed > 90 days         → STALE
  ├── marked_stuck or recovery_failed  → FAILED
  └── runtime_research_triggered       → RUNTIME_RESEARCH

STALE
  ├── refreshed successfully           → CACHED
  └── refresh errors                   → FAILED

FAILED
  ├── RDR priorities 1–5 resolve       → RUNTIME_RESEARCH
  ├── explicit clear                   → CACHED
  └── RDR priority 6 (recreate)        → deleted; new task

RUNTIME_RESEARCH
  ├── research complete & integrated   → CACHED
  └── research fails                   → FAILED
```

### STALE Detection

```python
def is_stale(item: WorkItem, ttl_days: int = 90) -> bool:
    age = datetime.utcnow() - parse_timestamp(item.cache_status.last_refreshed)
    return age.days > ttl_days
```

Repo convention matches Aperant: 90-day TTL for slowly-changing domain knowledge; shorter TTLs (7–30 days) for volatile data (e.g., vendor release notes, CVE catalogs).

## Stuck Sub-Task Detection

### Attempt History with Sliding Window

```python
def attempt_count(subtask_id: str, window_hours: int = 2) -> int:
    history = load_json("attempt_history.json")
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=window_hours)
    return sum(
        1 for ts in history.get(subtask_id, [])
        if parse_utc_timestamp(ts) > cutoff
    )

def mark_stuck(subtask_id: str, reason: str) -> None:
    # Clear history so next restart starts a fresh window
    history = load_json("attempt_history.json")
    history[subtask_id] = []
    write_json_atomic("attempt_history.json", history)

    plan = load_json("implementation_plan.json")
    set_subtask_status(plan, subtask_id, "failed", reason)
    write_json_atomic("implementation_plan.json", plan)
```

### Why the 2-Hour Sliding Window Matters

- Prevents stale attempts from prior sessions from inflating the retry counter.
- Crash + restart yields a **fresh** window, not an unbounded counter.
- Empirically tuned: shorter windows (30 min) caused false-stuck on legitimately long tasks; longer windows (24 h) let runaway loops persist.

### Hard Cap

- 50 attempts per sub-task, oldest-first eviction.
- A sub-task exceeding 50 attempts within a 2-hour window is assumed pathological and downgraded to `FAILED` regardless of last reason.

## Runtime JIT Research (Ephemeral)

### Strategy

When a cache state is `STALE` or agent confidence is low on an uncached topic:
1. Issue 2–3 web queries: one keyword-precise, one conceptual-synonym, optionally one cross-validation.
2. Fetch top 1–2 URLs per query (Jina Reader for technical content, WebFetch for lightweight).
3. Classify each source: **Tier 1** (official docs, peer-reviewed, standards), **Tier 2** (engineering case studies, benchmarks), **Tier 3** (tutorials, blogs without metrics).
4. Discard Tier-3 unless no Tier-1/2 available; never rely on a single Tier-3 source.
5. Inject as ephemera into agent context — **no disk persistence**.
6. Bound: max 3 research cycles per sub-task; flag unresolved if still incomplete.

### Ephemera Injection

```
## Runtime Research (this session only)

### Finding 1 — [title]
Source: {url}
Tier: {1|2|3}
Fetched: {timestamp}
Excerpt: {200–500 tokens, signal-dense extract}

### Finding 2 — ...
```

Agent treats these as *provisional* knowledge — lower confidence than cached knowledge, but higher than no knowledge. Any durable claim derived from research is marked for later distillation into the stable domain file.

### Tier Classification Shortcut

| Domain | Tier 1 signals |
|--------|----------------|
| Claude Code | docs.claude.com, code.claude.com, github.com/anthropics/claude-code |
| MCP | modelcontextprotocol.io, github.com/modelcontextprotocol |
| Academic | arxiv.org (with venue marker), dl.acm.org, ieeexplore |
| Standards | OASIS, IETF/RFC, W3C, ISO |

## RDR (Recover-Debug-Resend) Priorities

Aperant's 6-priority recovery ladder for failed sub-tasks:

| Priority | Action | When |
|----------|--------|------|
| 1 | Auto-continue | Skip the stuck sub-task, proceed with dependent work |
| 2 | Auto-recover | Internal fix attempt (retry with variant parameters) |
| 3 | Request changes | Surface to user via MCP for manual intervention |
| 4 | JSON fix | LLM-assisted schema-correction call |
| 5 | Manual debug | Expose logs, backtrace, full context to user |
| 6 | Recreate | Reset sub-task, restart from scratch |

Per-task RDR toggle:
- **Enabled**: failed sub-task holds its queue slot until resolved via MCP.
- **Disabled**: queue skips past failed tasks (async recovery).

This repo's review skills are all short-lived, so the full RDR ladder is not needed. Priorities 2, 4, and 6 are the usable subset (internal retry, LLM schema fix, and reset) — applicable inside `apply-*-review-findings` during Tier-2 recovery (see `research/fix-completeness/structured-output-recovery-patterns.md`).

## Adoption in This Repo

| Pattern | Roadmap slot | Notes |
|---------|--------------|-------|
| 4-state cache labels | P2.4 | Domain-cache files gain label + last_refreshed; `/check-repo-health` surfaces STALE count |
| Stuck-detection sliding window | Future (`/audit-session-trace` extensions) | Applicable if long-running skills emerge |
| Runtime JIT research | P2.6 | Fallback for primitive types not pre-cached; ephemeral injection |
| Tier classification | Already present | `research/source-quality/web-research-quality-evaluation.md` and Skill's existing source-quality-criteria |
| RDR priorities 2/4/6 | P1.2 (Tier-2 recovery) | Internal retry, LLM schema repair, reset |

## Sources

Tier 1:
- [Aperant PR #1813 — OOM handling, attempt history](https://github.com/AndyMik90/Aperant/pull/1813)
- [Aperant PR #1855 — MCP + RDR system](https://github.com/AndyMik90/Aperant/pull/1855)
- [Aperant PRs #1847 / #1853 — cache labels, self-healing](https://github.com/AndyMik90/Aperant)

Tier 2:
- Local research: `research/source-quality/web-research-quality-evaluation.md`
- Local research: `research/selective-context-injection/selective-context-injection-patterns.md`
