---
name: agent-composition-framework
description: SYNTHETIC RECOMMENDATION (components Tier-1 evidenced, composition unvalidated) for sub-agent prompt composition across role-spec × method × domain axes with Eager / Hint / JIT binding. Default `EHJ` is a default, not a proof. Load when scaffolding sub-agents, designing multi-agent dispatch, or evaluating sub-agent context composition.
last_refreshed: 2026-05-13
---

# Agent Composition Framework: WHO × HOW × WHAT × Binding

When the same sub-agent role (architect, staff engineer, security engineer) must be reused across multiple methods (PR review, design review, threat modeling) and multiple domains (Go, Python, Kubernetes), a naive Persona × Method × Domain matrix grows multiplicatively. This framework names three orthogonal axes and three binding strategies that decide where each axis lives in the prompt hierarchy.

The framework is a **synthetic recommendation** — its three constituent claims are each Tier-1 evidenced; the composition itself has not been validated as a unit. See §Empirical Validation Status.

## Three Axes

| Axis | What it captures | Example |
|---|---|---|
| **WHO** (Role-Spec) | Objective, output format, success criteria, constraints, tool grants — *behavioral*, not narrative | "Verify acceptance criteria; output JSON with severity field; cap at 5 findings" |
| **HOW** (Method) | Workflow, checklist, output schema for the *task type* | "PR review: 1) read diff, 2) apply rubric, 3) emit findings in canonical schema" |
| **WHAT** (Domain) | Language/framework idiom, tooling quirks, conventions | "Python: typing, asyncio TaskGroup, ruff configs, pyproject.toml" |

Three observations:

1. **WHO is *not* persona-narrative.** Empirical evidence — Cao/Sun/Yue arXiv:2602.12285 (AAAI 2026 TrustAgent Workshop, 26.2% degradation for demographic personas), Basil/Mollick arXiv:2512.05858 (expert personas don't improve factual accuracy on GPQA Diamond / MMLU-Pro across 6 models), Zheng arXiv:2311.10054 (EMNLP Findings 2024, minimum personas still degrade MMLU 71.6% → 68.0%) — disqualifies the narrative-persona form. The WHO axis captures *structured behavioral specification* per [`skill-agent-format-conventions.md` §Role Statements](../claude-code/skill-agent-format-conventions.md): `You are a <noun-phrase> that <verb-phrase>` + structured constraints.
2. **HOW is often persona-bound but conceptually orthogonal.** Some methods (PR review) are shared across roles; some (threat modeling) are role-specific. Default: treat as orthogonal until evidence collapses an axis.
3. **WHAT is the largest axis.** Languages, frameworks, infrastructure stacks — N can grow to 50+. JIT-loading wins on this axis.

## Binding Strategies (E / H / J)

For each axis, three binding points are available:

| Strategy | Where it lives | Cache footprint per N values |
|---|---|---|
| **E** Eager | System prompt | N cache slots |
| **H** Hint | User message (orchestrator-set) | 1 cache slot, ~50-200 tokens per task |
| **J** JIT | Skill metadata (level-1 progressive disclosure) + body load on demand | 1 cache slot for system; ~50 tokens metadata per skill; body cost only on activation |

Cache economics are load-bearing here, but cite carefully:

- **Anthropic prompt caching** (the runtime this repo's agents actually use): 10× cost-reduction on cached tokens, 5-min/1-hour TTL, breakpoint-hash invalidation. This is the load-bearing mechanism for the binding-strategy argument below. See [`aperant-orchestration-patterns.md`](../agent-knowledge-caching/aperant-orchestration-patterns.md).
- **KVFlow** (arXiv:2507.07400) measures 1.83× speedup for single workflows with large prompts and 2.19× speedup for many concurrent workflows vs SGLang hierarchical radix cache — an open-weight serving infrastructure, *not* Anthropic's cache. KVFlow is an **evidence anchor for the principle** that stable-prefix multi-agent workloads benefit measurably; it is **not** a directly applicable Claude Code number. The principle transfers; the magnitude does not without separate measurement.

The 27-combinations filter logic below relies on Anthropic-cache slot fragmentation (different system prompts → different cache slots → independent TTL warm-up). It does not rely on KVFlow's specific speedup magnitude.

## Default Recommendation (EHJ)

Notation: `<Persona-binding><Method-binding><Domain-binding>`. Default optimum: **`EHJ`** — Role-Spec Eager, Method Hint, Domain JIT.

Filter-down argument (27 combinations → 4 viable → 1 default):

1. **Persona Eager (Filter A)**: WHO is small-N (5-10 roles typical), needs full presence from turn 1, and is the natural unit for Claude Code's `agents/<role>.md` mechanism. Hint-Persona suffers from late identity activation; JIT-Persona forces a turn-1 self-load. → **Persona = E** (5-10 cache slots, not multiplied).
2. **Method × Domain Eager (Filter B)**: For 5 personas × 5 methods × 3 domains, `EEE` = 75 cache slots, `EE*` = 25, `E*E` = 15, `E**` = 5. Eager-Method or Eager-Domain fragments cache multiplicatively. → Method, Domain ∈ {H, J}.
3. **Method Hint vs JIT**: Method is typically known to the orchestrator (`Method: pr-review` from slash-command context). Hint is deterministic and auditable. JIT-Method risks wrong-workflow drift, which is high-cost (entire task pivots wrong direction). → **Method = H** by default.
4. **Domain JIT vs Hint**: Domain is often *not* known until the agent inspects files (mixed-language repos). Domain has large N (every language, every framework). Progressive Disclosure (level-1 description-only) makes JIT cheap. → **Domain = J** by default.

Result: `EHJ`.

## Failure Modes

| Failure | Cause | Mitigation |
|---|---|---|
| Wrong-skill-loaded | Description-graph collision or vague description | `make validate-descriptions` (description-graph validator) as a gate |
| Late-skill-loaded | Agent makes early decisions before Domain skill loads | Role-Spec instructs: "first action: identify primary language/framework and load matching skill" |
| Skill fan-out | Agent loads multiple skills "to be safe", burns context | Role-Spec limits to 2 Domain skills max |
| Method-Hint missed | Orchestrator forgets to name method | Slash-command template encodes method automatically |
| Wrong-method-routed | Method known but agent picks different workflow | Method-Hint is structured (`Method: pr-review`), not prose |
| Persona-Domain coupling | "Postgres-DBA" is sensibly fused | Don't force orthogonality where the world isn't orthogonal — collapse axes |

## When EHJ is NOT the optimum

`EHJ` is the default; specific situations shift it:

- **Single-language repo**: Domain is a repo property, not an agent property. Bind Domain via project `CLAUDE.md` → effectively `EH-` (Domain pre-bound at session level, not per-agent).
- **Security-critical review**: Force-include security overlay via Hint → `EHH`. "Agent must not forget" overrides cache cost.
- **Method genuinely ambiguous from task**: If the orchestrator does not know the workflow, Hint becomes a fiction → `EJJ`.
- **Very small matrix (N ≤ 2 in all axes)**: `EEE` overhead is negligible; determinism wins.
- **Persona-Domain naturally coupled** (Postgres-DBA, Kubernetes-Security-Engineer): collapse the coupled axes; don't force orthogonality.

## Empirical Validation Status

**[Synthetic recommendation — components verified, composition unvalidated]**

The three claims composing `EHJ` are each Tier-1 evidenced, with explicit scope:

| Claim | Evidence | Tier | Scope caveat |
|---|---|---|---|
| Narrative-persona prompts don't improve and can harm performance | Cao/Sun/Yue arXiv:2602.12285 (26.2%, AAAI 2026), Basil/Mollick arXiv:2512.05858 (GPQA Diamond + MMLU-Pro, 6 models), Zheng arXiv:2311.10054 (162 roles, 4 model families, EMNLP Findings 2024), Hu/Rostami/Thomason arXiv:2603.18507 (expert generative-vs-discriminative trade-off) | 1 | Studies test *narrative-demographic personas on factual MCQ benchmarks*. EHJ extrapolates to *behavioral role-specs in agentic code review*. Transfer is plausible but not measured. |
| JIT-retrieval beats eager pre-loading for variable context | Anthropic Effective Context Engineering doctrine | 1 (qualitative) | Anthropic's own doctrine, no quantitative effect-size cited. |
| Stable system-prompt prefix yields cache benefit in multi-agent workflows | KVFlow arXiv:2507.07400 (vs SGLang on open-weight serving) | 1 (principle only) | KVFlow's 1.83× / 2.19× magnitudes are *not* directly applicable to Anthropic's cache. The principle transfers; the magnitude needs separate measurement. |

The *combination* — choosing `EHJ` over `EHH`, `EJJ`, `EEH`, etc. — has not been directly evaluated in published literature as of 2026-05-13. A web search returned no study testing the persona × method × domain × binding-strategy matrix as such.

**Operational consequence**: treat any quoted EHJ performance number as theoretical until repo-internal eval-cases run. Empirical validation against this repo's `docs/review-eval-cases.md` is tracked separately as a future Wave 3 issue.

**Lock-in risk**: if a future Tier-1 study contradicts one of the three claims (e.g., narrative personas improve agentic-debugging tasks), the WHO-axis form-decision is not a hard rule — see §When EHJ is NOT the optimum. Cross-references to `engineering-baseline.md` and `skill-agent-format-conventions.md` provide the rule sources; if those sources are updated, this framework's claim shifts with them, not vice versa.

## Cross-References

- **WHO axis form (the rule)**: [`research/claude-code/skill-agent-format-conventions.md` §Role Statements](../claude-code/skill-agent-format-conventions.md). This framework defers to that rule; it does not re-derive it.
- **Cache economics**: [`research/agent-knowledge-caching/aperant-orchestration-patterns.md`](../agent-knowledge-caching/aperant-orchestration-patterns.md) (Anthropic-cache mechanics + KVFlow citation).
- **Persona evidence consolidated**: [`skills/review-claude-config/references/engineering-baseline.md`](../../skills/review-claude-config/references/engineering-baseline.md) §Role Priming. **Do not edit `engineering-baseline.md` mid-session** to align with this framework — Hard Constraint #6 in CLAUDE.md forbids it; baseline updates run via `/refresh-engineering-baseline` only. This framework is downstream of the baseline, not authoritative over it.
- **JIT-retrieval doctrine**: [`research/context-engineering/anthropic-effective-context-engineering.md`](../context-engineering/anthropic-effective-context-engineering.md).
- **Description routing determinism**: [`research/agent-skills/description-disambiguation.md`](description-disambiguation.md) (collision under contention).
- **Persona-magnitude verification status**: [`docs/research-backlog.md`](../../docs/research-backlog.md) entry #7.

## Sources

Tier 1:

- [Cao, Sun, Yue — "From Biased Chatbots to Biased Agents" (arXiv:2602.12285, AAAI 2026 TrustAgent Workshop)](https://arxiv.org/abs/2602.12285)
- [Basil, Shapiro, Mollick et al. — "Playing Pretend: Expert Personas Don't Improve Factual Accuracy" (arXiv:2512.05858)](https://arxiv.org/abs/2512.05858)
- [Zheng et al. — "When 'A Helpful Assistant' Is Not Really Helpful" (arXiv:2311.10054, EMNLP Findings 2024)](https://arxiv.org/abs/2311.10054)
- [Hu, Rostami, Thomason — "Expert Personas Improve LLM Alignment but Damage Accuracy: PRISM" (arXiv:2603.18507)](https://arxiv.org/abs/2603.18507)
- [KVFlow: Efficient Prefix Caching for LLM-Based Multi-Agent Workflows (arXiv:2507.07400)](https://arxiv.org/abs/2507.07400)
- [Anthropic — Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic — Equipping Agents for the Real World with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
