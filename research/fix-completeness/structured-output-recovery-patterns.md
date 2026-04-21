---
last_refreshed: 2026-04-19
---

# 3-Tier Structured-Output Recovery Patterns

Evidence-based recipe for making structured-output consumption robust across malformed model outputs. Feeds P1.2 (`report-parser-contract.md` under `skills/review-claude-config/references/`) and the `apply-*-review-findings` skill family.

## TL;DR

- Strict JSON/YAML parse fails in 5–15 % of LLM structured outputs depending on schema complexity and model class (Opus ~3–5 %, Sonnet ~6–8 %, Haiku ~10–12 %).
- A 3-tier cascade (strict → LLM-assisted minimal-schema extraction → regex text fallback) reduces total failure to <2 %.
- Aperant PR #1797 (merged 2026-02-12) is the production reference implementation.
- Tier-2 extraction success rate on minimal flat schemas: ~98 %.
- Blind self-correction without external validation degrades quality (arXiv:2310.01798) — Tier 2 must use a distinct schema, not ask the model to "fix its own output".

## Tier Cascade

### Tier 1 — Strict parse (happy path)

Validate full output against the production schema (Pydantic / JSON Schema / YAML spec).

- Success rate: model-dependent, 85–95 %.
- Fallback trigger: any schema validation exception.
- Zero additional API cost on success.

### Tier 2 — LLM-assisted minimal-schema extraction

On Tier-1 failure, issue a second API call with a **drastically reduced schema** (flat, ~7 fields) and a targeted extraction prompt.

Minimal schema for review-report consumers:

```
summary_items:        list[{type, path, score}]   # one per reviewed artifact
total_findings:       int
high_impact_count:    int
medium_impact_count:  int
recommendations_text: str                          # concatenated finding text
validation_warnings:  list[str]
confidence_score:     float                        # 0.0–1.0
```

Extraction prompt template (Aperant PR #1797):

```
Extract the key review data from the following AI analysis output.
Return: item paths, types, scores, finding counts, and concatenated
recommendation text.

--- REPORT ---
{report_text[:8000]}
--- END ---
```

- Success rate on minimal flat schemas: ~98 %.
- Added cost: ~$0.003 per invocation at Haiku tier.
- Fallback trigger: Tier-2 call errors, times out, or still fails schema validation.

Why this tier works:
1. Drastically reduced schema → fewer validation points.
2. Flat structure (no nested objects) → easier for the model to satisfy.
3. Text-window cap (8 K chars) → prevents token blow-up on retry.
4. Explicit extraction framing ("extract this data") → better adherence than "fix your previous output".

### Tier 3 — Regex text fallback (no LLM)

On Tier-2 failure, pull fields from the raw text with bounded regex patterns.

Example extractors:

| Target | Regex | Accuracy |
|--------|-------|----------|
| Verdict | `\b(approve\|request.changes?\|comment)\b` (case-insensitive) | ~85 % |
| Finding IDs | `(?:\[)?FINDING[_-]?(\d+)` | ~70 % |
| Section headers | `^#+\s+(.+)$` (multiline) | ~90 % |
| Paths | `^path:\s*(.+)$` (multiline) | ~95 % |
| Scores | `score:\s*([\d.]+)` | ~95 % |

- No API cost.
- Accuracy depends heavily on upstream formatting.
- Always succeeds in returning *something* — consumer marks result `validation: tier-3-recovered` and logs a warning.

### Cascade behavior

| Tier reached | Action | Log level |
|--------------|--------|-----------|
| Tier 1 | Use structured output as-is | none |
| Tier 2 | Use extraction result; skip detailed validation | warning `validated via tier-2 extraction` |
| Tier 3 | Use regex result; flag manual review | warning `validated via tier-3 text parsing; manual review recommended` |
| All fail | Halt, return error | error |

## Integration with `disable-model-invocation: true` Skills

The `apply-*-review-findings` family carries `disable-model-invocation: true`, meaning the skill itself cannot invoke the model for Tier-2 repair.

Workaround: delegate Tier-2 via `TaskCreate` to a dedicated `repair-structured-output` skill (model-invocation enabled).

Required pre-conditions for the apply-* skills:
- `allowed-tools` includes `TaskCreate`, `TaskGet`, `TaskUpdate`.
- Tier-2 Task dispatch carries `maxTurns: 5`, hard timeout 90 s.
- On Task timeout or failure → Tier-3 regex fallback (not another retry).

Trust-chain visibility:
- Hook matchers for `TaskCreated`/`TaskCompleted` (CLI v2.1.84+) extended in `delegation_tracker.py`.
- Full chain `apply-* → repair-structured-output → Task-Response` reconstructable from `$CLAUDE_PLUGIN_DATA/audit/`.

## Report-Parser-Contract Skeleton (for P1.2)

Planned at `skills/review-claude-config/references/report-parser-contract.md`.

Contract sections:
1. Tier 1 — strict parsing rules against `review-report-contract.md`.
2. Tier 2 — minimal-schema extraction via Task dispatch, including the 7-field schema above and the Aperant prompt template.
3. Tier 3 — regex recipes per extraction target.
4. Consumer behavior matrix (who logs what, who halts when).
5. Integration with `disable-model-invocation: true` constraint.

Referenced by: all five `apply-*-review-findings` skills.

## Evidence Summary

| Claim | Source | Tier |
|-------|--------|------|
| Structured-output error rates 5–15 % model-dependent | Instructor / LangChain empirics; engineering blogs | 2 |
| 3-tier cascade reduces failures <2 % | Aperant PR #1797 production telemetry | 2 (primary) |
| Blind self-correction degrades quality | [arXiv:2310.01798](https://arxiv.org/abs/2310.01798) (Huang et al., ICLR 2024) | 1 |
| K=2 detect-repair-verify yields 50–77 % | [arXiv:2406.01297](https://arxiv.org/abs/2406.01297) (Kamoi et al., TACL 2025) | 1 |
| Bounded iteration K=2–3 diminishing returns | arXiv:2603.00897 (ICSME 2025) | 1 |
| LLM-agent repair incompleteness 10–16 % | arXiv:2411.10213 (SWE-Agent / AutoCodeRover) | 1 |

## Open Questions

- Schema-minimality optimum (5 / 7 / 10 fields)? A/B testing recommended.
- Model-class-specific regex tuning for Tier 3 (Opus vs. Haiku output styles)?
- Cost-break-even point for Tier 2 vs. accepting Tier 3 accuracy?
- Feasibility of a router-LLM that predicts Tier-1 failure before the call is made?

## Sources

Tier 1:
- [arXiv:2310.01798 — Self-correction degrades without feedback](https://arxiv.org/abs/2310.01798)
- [arXiv:2406.01297 — Detect-Repair-Verify](https://arxiv.org/abs/2406.01297)
- [arXiv:2411.10213 — SWE-Agent / AutoCodeRover benchmarks](https://arxiv.org/abs/2411.10213)

Tier 2:
- [Aperant PR #1797 — 3-tier recovery for structured output validation failure](https://github.com/AndyMik90/Aperant/pull/1797) — merged 2026-02-12
- [Instructor (jxnl/instructor) retry docs](https://github.com/jxnl/instructor)
- LangChain, Outlines, Vercel AI SDK structured-output documentation
