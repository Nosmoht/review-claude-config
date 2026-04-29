---
name: rule-consolidation-vs-separation
description: Decision rules for skill-author choices on consolidating multiple rules into one vs separating them across body / references / sections, synthesized from 5 Tier-1 instruction-following benchmarks
last_refreshed: 2026-04-29
---

# Rule Consolidation vs Separation

When a skill carries N+ rules / constraints / instructions, the skill author must choose: **consolidate** related rules into one (denser, fewer items) vs **separate** them across sections, references, or distinct rules (sparser, more items). This file synthesizes 5 Tier-1 instruction-following benchmarks into actionable decision rules.

## Source-of-Truth Metrics

| Source | Headline finding relevant to consolidation/separation |
|---|---|
| AgentIF — arXiv:2505.16944 | Instruction Success Rate (ISR) drops to **<30% at avg 11.9 constraints**. Condition constraints fail at **19.1%** vs **66.8%** for formatting constraints. |
| IFScale — arXiv:2507.11538 | Two model-class behaviors: **linear-decay** (Claude Sonnet class) starts losing accuracy from the *first* density increase; **threshold-decay** (o3, Gemini-2.5-Pro) sustains near-perfect adherence through ~150+ instructions. |
| IFEval — arXiv:2311.07911 | 25 *verifiable* instruction types — programmatic checks eliminate LLM-judge bias when constraints are decomposable. |
| FollowBench — arXiv:2310.20410 | Multi-level mechanism: incrementally adding constraints reveals which constraint *types* break first. Condition / format adherence asymmetry confirmed. |
| ComplexBench — arXiv:2407.03978 | Four composition types: And, Chain, Selection, plus implicit. Selection (mutually-exclusive branches) and Chain (sequential dependencies) are highest-failure axes. |

## Decision Framework

The two axes that drive the consolidate-vs-separate decision:

1. **Constraint density** — how many distinct constraints does the agent need to track simultaneously? (AgentIF + IFScale)
2. **Constraint type** — are they format/utility (high adherence) or condition/composition (low adherence)? (FollowBench + ComplexBench)

### Rule 1 — Hard Cap on Body-Level Constraints

> If the body declares **>10 distinct constraints** (regardless of constraint type) AND target model is linear-decay class (Claude Sonnet/Opus 4.x), **separate** by moving stable knowledge into `references/` files via JIT loading.

Rationale: AgentIF establishes 11.9 as the ISR cliff for linear-decay models. Stay below it on the main body.

Mitigation if separation is impractical: structural sections (`## Hard Rules`, `## Workflow Steps`), priority ordering (most-critical first), few-shot examples. Per `scoring-rubric.md` §CE the mitigations downgrade the failure to `B` rather than `C`.

### Rule 2 — Conditional-Constraint Concentration

> If **>30% of body constraints are conditional** (`if X then Y` clauses) regardless of total count, **separate** the conditionals into a dedicated `## Decision Rules` or `## Conditional Branches` section, OR move them to a `references/decision-tree.md` JIT file.

Rationale: FollowBench + AgentIF show condition constraints at 19.1% adherence vs 66.8% for formatting. Concentrating them visually + structurally helps the agent locate them under attention budget.

### Rule 3 — Composition Disambiguation

> When ≥2 constraints could be interpreted as different composition types (And vs Chain vs Selection), **separate** the composition declaration into a single explicit marker line at the top of the constraint group.

Per ComplexBench: ambiguous composition is the failure mode. Mark explicitly:
- "Apply ALL of the following:" (And)
- "Apply IN ORDER:" (Chain — already covered by WS-1 numbered steps)
- "Select EXACTLY ONE:" (Selection — already covered by COMP-Sel)

### Rule 4 — Format/Utility Constraints Can Consolidate

> Format and utility constraints (output schema, naming convention, length cap) **may consolidate** into a single bullet point or table without separation cost.

Rationale: FollowBench shows format constraints at 66.8% adherence — high enough that consolidation does not push them below the C-grade threshold. Counter-evidence is rare; consolidate freely when constraints are mechanical-format-only.

### Rule 5 — Reasoning-Class-Model Exemption

> If the skill explicitly targets a **reasoning-class model** (o3, Gemini-2.5-Pro, future Anthropic reasoning model), Rule 1's >10-constraint cap is relaxed to ~150 per IFScale's threshold-decay calibration.

The `## Model Targeting` block in the skill's frontmatter or a dedicated body section should state the assumption explicitly. Without explicit targeting, default to linear-decay assumptions (Claude 4.x is linear-decay class).

## Worked Examples

### Consolidation example — formatting constraints

```markdown
## Output Format
- Each finding: `Current:` block, `Recommended:` block, `Validation:` line
- Maximum 200 chars per block
- No emoji, third-person prose
```

Three formatting constraints consolidated into one section. Rule 4 — acceptable, no degradation expected.

### Separation example — conditional constraints

**Anti-pattern** (concentrated, no structural separation):

```markdown
## Workflow
- Read the file. If frontmatter is missing, abort. If the file is >500 lines, warn. If the file uses `name:` not `id:`, treat as legacy. If the YAML is malformed, fall through to default. If the path doesn't end in `.md`, skip.
```

Five condition constraints in one paragraph. Per Rule 2: separate.

**Pattern** (separated):

```markdown
## Workflow
1. Read the file.
2. Apply preconditions per § "Decision Rules" below.
3. Process per § "Main workflow".

## Decision Rules
| Condition | Action |
|---|---|
| Frontmatter missing | Abort with error |
| File >500 lines | Warn but continue |
| Uses `name:` not `id:` | Treat as legacy mode |
| YAML malformed | Default to baseline |
| Path doesn't end `.md` | Skip with status: skipped |
```

Five conditions in a structured table. Easier for the agent to enumerate; passes Rule 2 mitigation.

### Composition disambiguation example

**Anti-pattern**:

```markdown
- If user passes `--review`, run review-skill.
- If user passes `--audit`, run audit-repo.
- If user passes `--scaffold`, run scaffold-skill.
```

Three branches, no marker. ComplexBench failure mode: agent could fire all three under flag combinations.

**Pattern**:

```markdown
**Select EXACTLY ONE based on first matching flag:**
- `--review` → run review-skill
- `--audit` → run audit-repo
- `--scaffold` → run scaffold-skill
- (none) → prompt user via AskUserQuestion
```

Composition explicit (Selection); first-match-wins explicit; default branch named.

## Rubric Cross-References

Rules synthesized here back the following existing rubric items:

| Rule | Backed by rubric item |
|---|---|
| Rule 1 (Hard cap >10) | CE narrative §C-test (line 41 — AgentIF citation) |
| Rule 2 (Condition concentration >30%) | CE narrative §C-test (line 41 — same) |
| Rule 3 (Composition disambiguation) | COMP-Sel (issue #96) + WS-1/WS-3 (sequencing markers) |
| Rule 4 (Format consolidation) | No rubric item — guidance only (consolidation is permission, not mandate) |
| Rule 5 (Reasoning-model relaxation) | CE narrative §C-test model-taxonomy note (line 45 — IFScale citation) |

No new rubric items added by this synthesis. The decision-framework is *descriptive* — it tells skill authors how to make the consolidate-vs-separate choice such that existing rubric items pass.

## Self-Application

The repo's existing skills already follow these rules informally:
- `review-skill` body has 17 numbered steps split across multiple `Phase` sections + heavy `references/` usage (Rules 1, 2 satisfied via separation)
- `audit-repo` keeps formatting constraints in tables (Rule 4) and separates conditional branches into `## Decision` blocks (Rule 2)
- `scaffold-skill` uses sequential step numbering (Rule 3 Chain) and the mode parser uses token-equality dispatch (Rule 3 Selection NA-exempt)

No fix commits triggered by this synthesis. The document codifies existing successful patterns and prevents drift in future skills.

## References

- arXiv:2505.16944 — Liu et al., AgentIF (instruction-following-at-scale benchmark)
- arXiv:2507.11538 — IFScale model taxonomy
- arXiv:2311.07911 — Zhou et al., IFEval (Google)
- arXiv:2310.20410 — Jiang et al., FollowBench (ACL 2024)
- arXiv:2407.03978 — Wen et al., ComplexBench (NeurIPS 2024 Datasets and Benchmarks Track)

## Repo Cross-References

- `research/instruction-following/instruction-following-at-scale.md` — AgentIF / IFScale source file
- `research/instruction-following/benchmark-comparison.md` — IFEval / FollowBench / ComplexBench comparison from issue #96
- `skills/review-claude-config/references/scoring-rubric.md` §CE C-test (line 41) and §COMP-* — rubric items backed by these sources
- `skills/review-claude-config/references/engineering-baseline.md` §"Constraint Load" — adjacent baseline guidance
