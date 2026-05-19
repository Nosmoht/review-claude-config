# Evidence Maintenance Guide

This guide tells maintainers how to classify claims in `review-claude-config` without overstating certainty.

## Use the Canonical Contract

Repository-level evidence classification is defined in [`evidence-contract.md`](../skills/review-claude-config/references/evidence-contract.md).

Use only these classes:

- `Proven result`
- `Engineering guidance`
- `Repo default`
- `Low-evidence area`

Do not introduce alternate labels in top-level docs or shared references.

## How to Classify a Claim

### Proven result

Use when the claim is directly supported by Tier 1 evidence.

Examples in this repo:

- Domain knowledge can materially improve agent quality.
- Focused context management matters for agent performance.

### Engineering guidance

Use when official guidance or credible technical literature supports the pattern, but the result is not a strong universal benchmark claim.

Examples in this repo:

- Use minimal tool sets and explicit tool descriptions.
- Use Claude Code hooks for lightweight guidance and session checks.

### Repo default

Use when the repository chooses a convention or threshold for operational reasons.

Examples in this repo:

- Path-first identity in review analytics.
- Repo-specific token budgets or refresh workflows when they are not directly benchmark-backed.

### Low-evidence area

Use when the subsystem is useful but direct literature is thin or mostly heuristic.

Examples in this repo:

- Skill-gap detection as a general method.
- Primitive derivation from repository signals into Claude Code primitives.

## Mapping Older Wording

| Old wording | Replace with |
|---|---|
| Local design preference | Repo default |
| local policy | Repo default |
| heuristic / novel contribution / limited evidence | Low-evidence area |

## Maintainer Rules

- If a stronger source contradicts a local summary, update the local wording and record the contradiction rather than hiding it.
- If a claim cannot be defended with Tier 1 or strong Tier 2 evidence, do not present it as settled fact.
- If a rule is primarily chosen for this repo’s workflow, label it `Repo default`.
- When in doubt between `Engineering guidance` and `Repo default`, use `Repo default` unless the guidance clearly comes from an authoritative external source.

## Dossier and Research Lifecycle

Use this section as the single maintenance-process authority for the wider evidence layer.

### Cadence

- Review `docs/scientific-research-dossier.md`, `docs/repo-gap-analysis.md`, and `docs/evidence-backed-refactor-plan.md` every 90 days.
- Use the same 90-day rhythm as the repo's baseline freshness discipline, but keep this process manual.

### Triggers

Run an evidence-layer maintenance pass when any of these happen:

- the scheduled 90-day review comes due
- `docs/scientific-research-dossier.md` is edited
- a source cited in the dossier is added or replaced
- a stronger source contradicts a cited local summary

### Ownership and Precedence

- Evidence-layer upkeep is manual maintainer work, not skill ownership.
- `refresh-engineering-baseline` remains limited to `engineering-baseline.md`.
- Local `research/*` provenance annotations are source metadata only.
- Repo-level interpretation lives in [`evidence-contract.md`](../skills/review-claude-config/references/evidence-contract.md) and [`scientific-research-dossier.md`](scientific-research-dossier.md).
- Record contradictions canonically in `docs/scientific-research-dossier.md`, not in local research summaries.

### Normalization Checks

- Use only the canonical class names from `evidence-contract.md` for repo-level claims.
- Treat [`evidence-contract.md`](../skills/review-claude-config/references/evidence-contract.md) and [`review-report-contract.md`](../skills/review-claude-config/references/review-report-contract.md) as the only relevant contract authorities in this area.
- Before finalizing edits, search for non-canonical class names in `docs/` and `research/`.

## Ongoing Maintenance

- keep [`engineering-baseline.md`](../skills/review-claude-config/references/engineering-baseline.md) explicitly evidence-classified
- keep the baseline refresh path aligned with the canonical evidence contract and shared source-quality criteria
- keep maintainer guidance files such as [`CLAUDE.md`](../CLAUDE.md) consistent with the active evidence vocabulary and runtime behavior

## Quartärly Evidence-Coverage Cadence

The `docs/dimension-evidence-coverage.md` matrix is a maintained living artifact, re-audited every 90 days (matches the `domain-cache` rhythm). The audit looks for new Tier-1 sources per dimension that have appeared since the last audit and integrates them into rubric or research files.

### Cadence

- **Period**: 90 days. Set the next audit's target date when each audit completes.
- **Trigger**: maintainer runs `/refresh-evidence-coverage [dimension]` (skill at `skills/refresh-evidence-coverage/`). Without arguments, the skill iterates all 7 dimensions.
- **Out of scope**: auto-running via CI. Refresh is maintainer-triggered, like `/refresh-engineering-baseline`.

### Per-Dimension Search Strategy

| Dimension | Primary search anchors | Last anchored to |
|---|---|---|
| Clarity | "LLM linguistic robustness", "negation/quantifier reasoning benchmark", "psycholinguistic diagnostics" | Truong / oLMpics / HANS / Kassner-Ettinger |
| Completeness | "instruction-following benchmark", "constraint composition", "verifiable instructions" | AgentIF / IFScale / IFEval / FollowBench / ComplexBench |
| Prompt Engineering | "prompt engineering techniques empirical", "few-shot scaling", "verification chain LLM" | CoVe (Dhuliawala) |
| Context Engineering | "long-context attention bias", "lost-in-the-middle", "context-rot benchmark" | Liu et al. + Ms-PoE |
| Goal Alignment | "sycophancy LLM", "goal misgeneralization RL", "specification gaming reasoning models" | Sharma / Langosco-Shah / Bondarenko |
| Safety | "tool misuse benchmark", "indirect prompt injection agent", "agent adversarial robustness" | ToolEmu / AgentDojo / InjecAgent + MAST + Progent |
| Metadata | "tool selection accuracy similar tools", "skill routing benchmark", "description disambiguation" | MetaTool / ToolLLM / Gorilla |

### Audit Output

Each audit produces:
1. Updated `last_audited:` per-dimension date in `docs/dimension-evidence-coverage.md`
2. New research files for any qualifying Tier-1 sources discovered (under `research/<domain>/`)
3. Optional rubric/baseline updates if the new sources operationalize a failure mode (separate atomic commits per the existing rubric-edit discipline)
4. CLAUDE.md research-references entries for new files
5. Follow-up issue per dimension where the audit surfaced new sources but operationalization is non-trivial — defer per the #91-cycle pattern

### Tier-1 Filter (recap)

Per the global `web-research.md` rule and `skills/review-claude-config/references/source-quality-criteria.md`:
- arXiv preprints, peer-reviewed conference/journal papers, RFCs/specs, foundation-lab publications (Anthropic / DeepMind / OpenAI / CNCF / OWASP)
- ≥50 citations OR ≤18 months old (foundational papers exempt from freshness rule)
- 2+ independent sources per claim (web-research rule)
