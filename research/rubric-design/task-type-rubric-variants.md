---
last_refreshed: 2026-04-19
---

# Task-Type Rubric Variants

Override tables and resolution algorithm for task-type-specific rubric application. Companion to `rubric-calibration-evidence.md` (issue #10). Referenced from `skills/review-claude-config/references/scoring-rubric.md`.

## Purpose

A single fixed 7-dimension rubric penalizes specialized skill designs and produces correlation r≈0.63 with human judgment. Task-type-adaptive rubrics reach r≈0.79 (AdaRubric, arXiv:2603.21362). Instead of rewriting the core rubric per task type, we publish **override tables** that adjust dimension weight or swap-in task-specific sub-criteria.

The core 7 dimensions (Clarity, Completeness, Prompt Engineering, Context Engineering, Goal Alignment, Safety, Metadata) remain stable. Task type determines which dimensions carry elevated weight and which sub-criteria apply within them.

## Resolution Algorithm (heuristic-first, reviewer-override)

Executed before dimension scoring begins:

```
1. Apply deterministic heuristics (no LLM):
   - allowed-tools contains Write AND Bash  → {scaffold, orchestrator}
   - allowed-tools contains TaskCreate       → orchestrator
   - name matches ^review-|^audit-|^classify- → code-review
   - name matches ^research-|^sync-|^refresh- → research-synthesis
   - name matches ^scaffold-|^develop-|^apply- → scaffold
   - name matches ^guide-|^explain-|^teach-   → tutoring

2. If reviewer supplied --task-type=<type> → use that verbatim.

3. If heuristics produce ≥2 candidates:
   - Invoke single LLM-binary call with description + allowed-tools + top 2 candidates.
   - Return the chosen type + one-sentence justification.
   - Log both to the report certificate.

4. If no heuristic matches and no override:
   - Default to "general-purpose" (no task-type override applied).
   - Warn in report that task-type could not be resolved.
```

Fail-open behavior: when in doubt, skip the override and apply the base rubric unchanged. Overrides never reduce strictness below the base rubric.

## Override Tables

### Agentic orchestrator (skills that delegate to sub-agents)

Identifying signals: `allowed-tools` includes `TaskCreate`; body contains multi-step delegation language.

| Dimension | Emphasis | Sub-criteria to add |
|-----------|----------|----------------------|
| CE | **high** | Subagent-contract clarity; delegation scope per sub-task; failure-path declaration; max-turn discipline |
| GA | **high** | Task decomposition accuracy; routing correctness per sub-agent |
| Safety | **high** | Sub-agent tool grants explicit; least-privilege observed; trust-chain depth bounded |
| PE | medium | Standard |
| Clarity | medium | Standard |
| Completeness | medium | Success criteria at orchestrator level |
| Metadata | low | Standard |

De-emphasized: JIT retrieval per call, minimal toolset (orchestrators legitimately carry many tools).

### Code review / analysis (skills that evaluate or audit code/config)

Identifying signals: name prefix `review-|audit-|classify-`; `allowed-tools` tends to `Read, Grep, Glob`.

| Dimension | Emphasis | Sub-criteria to add |
|-----------|----------|----------------------|
| CE | **high** | Token density; minimal toolset; focused tooling; intentionally-small context is GOOD |
| GA | **high** | Domain expertise coverage (language + framework patterns); analysis completeness |
| Safety | **high** | Read-only invariant; no Write/Edit/Bash unless justified |
| PE | medium | Standard; boundary exemplars for grading |
| Clarity | medium | Standard |
| Completeness | medium | Finding schema completeness, report contract compliance |
| Metadata | low | Standard |

De-emphasized: tool diversity (small allowed-tools is a feature, not a bug).

### Research synthesis (skills that gather and distill information)

Identifying signals: name prefix `research-|sync-|refresh-`; `allowed-tools` includes `WebSearch` or `WebFetch`.

| Dimension | Emphasis | Sub-criteria to add |
|-----------|----------|----------------------|
| CE | **high** | JIT retrieval discipline; source-quality classification; citation management; 3-cycle research cap |
| GA | **high** | Synthesis completeness; argument structure; novelty integration vs. existing knowledge |
| PE | **high** | Query formulation; iterative-retrieval discipline |
| Safety | medium | Source-quality tiers enforced; no Tier-3-only claims |
| Clarity | medium | Standard |
| Completeness | medium | Source diversity; cross-validation evidence |
| Metadata | low | Standard |

De-emphasized: minimal toolset (research legitimately needs broad tool diversity).

### Scaffold / template (skills that generate new artifacts)

Identifying signals: name prefix `scaffold-|develop-|apply-`; `allowed-tools` includes `Write`.

| Dimension | Emphasis | Sub-criteria to add |
|-----------|----------|----------------------|
| Completeness | **high** | Output schema completeness; type safety of generated artifact |
| GA | **high** | Template correctness; example variety; output matches stated archetype |
| Clarity | **high** | Generated-artifact readability |
| Safety | **high** | Write path confinement; no overwrites of user content without consent |
| PE | medium | Standard |
| CE | low | Scaffold skills legitimately carry large reference/template files |
| Metadata | low | Standard |

De-emphasized: CE token density (templates ARE the content).

### Interactive tutoring (skills that teach or explain)

Identifying signals: name prefix `guide-|explain-|teach-`; description mentions user dialogue.

| Dimension | Emphasis | Sub-criteria to add |
|-----------|----------|----------------------|
| PE | **high** | Progressive disclosure; error recovery; feedback quality; misconception addressing |
| Clarity | **high** | Pedagogical structure; reading level; example progression |
| GA | **high** | Learning objectives stated; check-for-understanding mechanisms |
| CE | medium | Standard |
| Completeness | medium | Coverage of learning objectives |
| Safety | low | Standard |
| Metadata | low | Standard |

De-emphasized: CE minimal toolset (tutoring may invoke multiple tools for demonstration).

## Non-Overrides

Some dimensions never get de-emphasized below the base rubric:

- **Safety** — always at or above base for any skill with `Write`, `Edit`, `Bash`, or `mcp__*` tools.
- **Metadata** — description trigger consistency (META-1/2/3) is universal.
- **Completeness** — success-criteria items (COMP-X/Y/Z) apply regardless of task type.

## Adoption Constraints

- Override tables operate as **weighting hints** to the scorer, not hard rule replacements.
- A skill graded via task-type override must include in its report: `task_type_resolved: <type>` and `task_type_resolution: {heuristic | override | llm-binary}`.
- On ambiguity between two plausible task types, the stricter table wins.
- Override tables are reviewed quarterly alongside the core rubric for drift.

## Evidence

- [arXiv:2603.21362 — AdaRubric](https://arxiv.org/abs/2603.21362) — task-adaptive rubrics r=0.79 vs r=0.63 fixed. Krippendorff α=0.83. Tier 1.
- [arXiv:2603.25133 — RubricEval](https://arxiv.org/abs/2603.25133) — three hardest rubric categories (Format Structure, Task Completion, Role/Persona) vary by task type. Tier 1.

## See Also

- `research/rubric-design/rubric-calibration-evidence.md` — primary evidence for all rubric changes in P0.5.
- `skills/review-claude-config/references/scoring-rubric.md` — core rubric; links here for task-type guidance.
