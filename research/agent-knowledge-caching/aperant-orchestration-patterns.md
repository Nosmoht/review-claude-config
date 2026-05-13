---
last_refreshed: 2026-05-13
---

# Aperant Orchestration Patterns: Shared-Prefix, KV-Cache, Atomic Writes

Patterns distilled from AndyMik90/Aperant (production autonomous-coding framework) for adoption in this review plugin. Covers shared-prefix construction for multi-perspective review, KV-cache hit economics, atomic file writes for report persistence.

## TL;DR

- Anthropic prompt cache minimum is **4,096 tokens for Opus** (4.7/4.6/4.5), **1,024 tokens for Sonnet**, **4,096 tokens for Haiku 4.5**. Sub-threshold prompts silently skip caching.
- Cache-hit cost is **10 % of base input** (90 % savings); cache-write costs **125 % of base** (1.25×). Break-even at ~12 hits.
- Shared-prefix hierarchy: `tools → system → messages`. Any content-drift at a cache breakpoint invalidates downstream cache.
- Atomic writes: `write tmp file → fs.rename` is atomic on POSIX; retry wrapper for EBUSY/EACCES/EAGAIN prevents 0-byte corruption.
- Aperant adopted this for `implementation_plan.json`, `task_metadata.json`, `project-store.ts` (PR #1785, merged 2026-02).

## Anthropic Prompt Cache Mechanics

### Hash Matching

- Cumulative SHA-256 hash of the prompt up to each `cache_control` breakpoint.
- 100 % identical blocks required — a single-character drift invalidates the cache for that breakpoint and everything after.
- Lookback window: ~20 blocks scanned for prior cache writes.

### Cacheable Content

- Tools, system messages, text blocks, images, documents, tool-use results.
- **Not cacheable**: thinking blocks (sit as separate top-level), sub-content blocks, empty blocks.

### Minimum Thresholds

| Model | Minimum tokens |
|-------|----------------|
| Opus 4.7 / 4.6 / 4.5 | 4,096 |
| Sonnet 4.5 / 4 | 1,024 |
| Haiku 4.5 | 4,096 |

Sub-threshold fails silently — `cache_creation_input_tokens == 0` in the response is the only signal.

### Cache-Break Triggers

| Change source | Tools | System | Messages |
|---------------|-------|--------|----------|
| Tool-definition edit | ✓ | ✗ | ✗ |
| Web-search toggle | ✓ | ✗ | ✗ |
| Tool-choice change | ✓ | ✓ | ✗ |
| Image add/remove | ✓ | ✓ | ✗ |
| Content at breakpoint | ✓ | ✓ | ✓ |

✓ = break happens if the row-change occurs at or above this hierarchy level.

**Critical anti-pattern**: `cache_control` markers on dynamic content (timestamps, counters, request IDs) → cache miss every request.

## Cost Economics

```
Base input:           $  5.00 / M tokens
Cache write (5 min):  $  6.25 / M tokens (1.25×)
Cache hit:            $  0.50 / M tokens (0.10× — 90% savings)

Example: 100 K cached tokens
- Uncached:  $500
- Cache hit: $ 50
- Savings:   $450 per hit
```

Break-even vs. no-cache: approximately **12 hits** amortizes the 1.25× write premium, then every subsequent hit is pure savings.

## Shared-Prefix Construction (deterministic)

For multi-perspective review (P1.1 in this repo's roadmap):

1. **Static-first ordering**: tools → system-prompt → reference-material (rubric, baseline, source-quality criteria).
2. **Append-only message history**: deterministic serialization (YAML/JSON, alphabetized keys), no mutation of prior turns.
3. **Session routing**: identical session-IDs route to the same worker for consistent cache warmth.
4. **Explicit breakpoint discipline**: mark `cache_control` only on stable content; never on per-request data.

Measured shared-prefix size for this repo (2026-04-19, Opus 4.7 tokenizer):
- `scoring-rubric.md` ~1,930 tokens
- `engineering-baseline.md` ~2,575 tokens
- `source-quality-criteria.md` ~415 tokens
- Perspective-wrapper ~300 tokens
- **Total: ~5,220 tokens** → qualifies for Opus cache (≥4,096) with ~25 % headroom.

Hard floor: **4,200 tokens** to preserve cache qualification under future trim.

## Multi-Agent Cache Benefits (Academic Evidence)

Aperant's pricing-side numbers (10× cache-hit cost reduction) come from Anthropic platform docs. The independent academic anchor for **multi-agent-specific** cache speedup is KVFlow ([arXiv:2507.07400](https://arxiv.org/abs/2507.07400)):

- **1.83× speedup** for single workflows with large prompts vs SGLang hierarchical radix cache.
- **2.19× speedup** for scenarios with many concurrent workflows.
- Targets exactly the shared-prefix + many-subagent pattern this repo uses for multi-perspective review.

This is a Tier-1 evidence anchor that supports the broader EHJ composition framework's Domain-JIT axis (stable system-prompt prefix across persona × language × method combinations). Note: a previously considered citation (Sinha personal blog, "F5 — Squashing Bugs", 39-64 % TTFT improvement, GPT-4.1-mini, N=60) was downgraded to Tier 3 on inspection (single-individual experiment, no peer review) and is explicitly excluded.

## KV-Cache Hit Metrics (monitoring)

Track per perspective-subagent call:

```
cache_hit_rate =
  cache_read_input_tokens / (cache_read_input_tokens + input_tokens)

cache_write_cost  = cache_creation_input_tokens × $6.25 / M
cache_read_saving = cache_read_input_tokens × $4.50 / M (Δ vs base)

turnaround_vs_uncached = target < 30 % of uncached latency
```

Target hit rate for repeatedly-invoked prompts (review workflows): **>80 %**. Lower values signal either cache-breakpoint drift or insufficient workflow repetition.

## Atomic File Write Pattern (Aperant PR #1785)

Problem: `fs.writeFileSync()` truncates before writing — a crash mid-write leaves a 0-byte file.

Solution: write to temp file, then atomic rename.

### TypeScript (Aperant reference)

```typescript
import * as fs from "node:fs";
import * as crypto from "node:crypto";
import * as path from "node:path";

export async function writeFileAtomic(
  filePath: string,
  data: string | Buffer,
  encoding: BufferEncoding = "utf-8"
): Promise<void> {
  const dir = path.dirname(filePath);
  const tempFile = path.join(dir, `.tmp-${crypto.randomBytes(8).toString("hex")}`);
  try {
    await fs.promises.writeFile(tempFile, data, encoding);
    await fs.promises.rename(tempFile, filePath);   // atomic on POSIX
  } catch (error) {
    await fs.promises.unlink(tempFile).catch(() => {});
    throw error;
  }
}
```

### Retry Wrapper (transient errors)

```typescript
async function writeFileWithRetry(
  filePath: string,
  data: string | Buffer,
  { maxRetries = 3, baseDelay = 100 } = {}
): Promise<void> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try { return await writeFileAtomic(filePath, data); }
    catch (e: any) {
      const transient = ["EBUSY", "EACCES", "EAGAIN", "EPERM", "EMFILE", "ENFILE"].includes(e.code);
      if (!transient || attempt === maxRetries) throw e;
      await new Promise(r => setTimeout(r, baseDelay * 2 ** attempt));
    }
  }
}
```

### Python Equivalent

```python
import os, tempfile
from pathlib import Path

def write_file_atomic(path: Path, data: str, encoding: str = "utf-8") -> None:
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)   # atomic on POSIX, atomic-best-effort on Windows
    except Exception:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise
```

Aperant applies this to `implementation_plan.json`, `task_metadata.json`, `project-store.ts` — highest-write-traffic files where 0-byte corruption has been observed in practice before the fix.

## Adoption in This Repo

| Pattern | Roadmap slot | Rationale |
|---------|--------------|-----------|
| Shared-prefix construction | P1.1 (multi-perspective review) | Enables Trust-or-Escalate 1.35× cost model |
| KV-cache metrics monitoring | P1.1 verification | Measures actual cache-hit rate against 80 % target |
| Atomic writes | P2.7 | Report persistence robustness; `.claude/reviews/` currently vulnerable |
| Break-even cost model | Roadmap risk section | Guides Opus 4.7 tokenizer drift mitigation in P0.5 |

## Sources

Tier 1:
- [Anthropic Prompt Caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — accessed 2026-04-19
- [Aperant PR #1785 — atomic file writes](https://github.com/AndyMik90/Aperant/pull/1785) — merged 2026-02
- [KVFlow: Efficient Prefix Caching for Accelerating LLM-Based Multi-Agent Workflows (arXiv:2507.07400)](https://arxiv.org/abs/2507.07400) — 1.83× / 2.19× speedup vs SGLang hierarchical radix cache

Tier 2:
- [Manus: Context Engineering Lessons](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) — "KV-cache hit rate = single most important metric"
- Local research: `research/agent-knowledge-caching/llm-agent-caching-patterns.md`
