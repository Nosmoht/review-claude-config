---
name: lost-in-the-middle
description: Liu et al. position-bias finding (LiM effect) — LLMs use long-context information unevenly with U-shaped attention; foundational for instruction placement in skill artifacts
last_refreshed: 2026-04-29
---

# Lost-in-the-Middle (LiM) Effect

## Definition

LLMs exhibit U-shaped attention over long input contexts: performance is highest when relevant information occurs at the *beginning* or *end* of the input, and degrades significantly when relevant information must be retrieved from the *middle* of long contexts. The effect persists across model families and scales — including explicitly long-context models — and worsens as input length grows.

For skill artifacts, this means: a critical hard constraint placed in the middle of a 500-line skill body is materially less likely to be followed than the same constraint placed at the beginning or end.

## Tier-1 Evidence

### Liu et al. 2023/2024 — Original Paper

- **Source**: Liu, Lin, Hewitt, Paranjape, Bevilacqua, Petroni, Liang. *Lost in the Middle: How Language Models Use Long Contexts*. arXiv:2307.03172. Published in TACL 2024 (https://aclanthology.org/2024.tacl-1.9/).
- **Method**: Two long-context tasks — multi-document question answering, key-value retrieval. Vary the position of the relevant document/key across input contexts of varying length.
- **Headline findings**:
  - Performance is highest when relevant information is at the **beginning** or **end** of the context.
  - Performance significantly degrades when relevant information is in the **middle**.
  - The U-shaped degradation persists even for explicitly long-context models (e.g., GPT-3.5-Turbo-16k, Claude 1.3-100k).
  - Performance also decreases substantially as overall input length grows, regardless of position.
- **Code+data**: https://github.com/nelson-liu/lost-in-the-middle.

### Cross-Validation: "Found in the Middle" — Plug-and-Play Mitigation

- **Source**: Zhang et al. 2024. *Found in the Middle: How Language Models Use Long Contexts Better via Plug-and-Play Positional Encoding*. arXiv:2403.04797.
- **Method**: Introduces Multi-scale Positional Encoding (Ms-PoE) to mitigate LiM via position-index rescaling.
- **Headline finding**: The LiM effect is real and measurable — Ms-PoE provides plug-and-play mitigation, validated on Zero-SCROLLS benchmarks, multi-document QA, and key-value retrieval. Confirms the original Liu et al. characterization.

### Additional Corroboration

- *Found in the Middle: Calibrating Positional Attention Bias* — arXiv:2406.16008 (ACL 2024 Findings) — independent calibration approach validates the position-bias problem.
- *Attention Instruction: Amplifying Attention in the Middle via Prompting* — arXiv:2406.17095 — prompting-time mitigation proves the effect is sufficiently robust to require prompt-level workarounds.

## Manifestation in Claude Code Skill Artifacts

The consumer LLM reads skill bodies as input context. If a skill body is longer than ~200 lines, the LiM effect predicts that critical instructions placed in the middle (lines ~80-160 in a 200-line body) will be applied less reliably than instructions in the first 20% (~lines 1-40) or last 20% (~lines 160-200).

**Anti-patterns**

- Critical hard constraints (e.g., "MUST NOT modify X", "ALWAYS validate Y") placed in the middle of a long workflow.
- Required setup steps buried in the middle of phase descriptions while less-critical formatting guidance bookends the file.
- Single-mention placement of a constraint that the agent must apply throughout the workflow.

**Mitigating patterns**

- Hard constraints declared in a "Hard Rules" / "Critical Constraints" section at the top of the body (after frontmatter), AND repeated in a closing "Reminder / Pre-Emit Checks" section.
- Critical placement test: walk the body in line order; if a constraint is required for step N, the constraint should appear before or at step N's line position, ideally also at the start of the file.
- Aggressive use of `references/` files for stable knowledge; main body stays under ~200 lines so the U-shape compresses to a single inflection.

## Operationalization Pattern

### CE-CP Critical-Instruction-Placement (new item)

**Iff-predicate (LLM-binary)**

> If the body is ≥150 lines AND contains explicit "critical" / "MUST" / "MUST NOT" / "ALWAYS" / "NEVER" / "Hard Rule" / "Critical Constraint" markers, each marked constraint is positioned in either the first 20% of the body OR the last 20% OR is duplicated such that at least one occurrence falls in those zones. Constraints appearing only in the middle 60% of a ≥150-line body without duplication → Context Engineering capped at C.

**Verification (LLM-binary)**:
1. Compute body line count after frontmatter.
2. Identify constraint markers via regex `/\b(MUST|MUST NOT|NEVER|ALWAYS|CRITICAL|Hard Rule|Critical Constraint)\b/`.
3. For each marker, compute its position as line_number / total_lines.
4. PASS if the marker is at position ≤0.20 OR ≥0.80, OR if the same constraint text appears at both a middle and an edge position.
5. **NA exemption**: bodies <150 lines are NA (LiM effect does not meaningfully apply at short contexts; positioned matters less than presence).

**PASS examples**

- Skill body has a "Hard Rules" section at lines 8-25 listing all MUST NOT items, then repeats the most critical rules in a "Pre-Emit Checks" section at lines 380-400 of a 400-line body.
- 100-line skill body — NA.
- 250-line skill body with `MUST NOT modify shared state` appearing at line 12 and line 230 (both within first/last 20%).

**FAIL examples**

- 300-line skill body with `MUST validate input` appearing only at line 145 (middle 60%, no duplication).
- 500-line skill body with all "CRITICAL" markers concentrated in lines 200-300.

Source: arXiv:2307.03172 (Liu et al. TACL 2024 — U-shaped attention); cross-validation arXiv:2403.04797 (Zhang et al. — Ms-PoE mitigation confirms effect).

## Self-Application Audit (2026-04-29)

Refined predicate: CE-CP triggers only on Hard-Rules-class section headers (e.g., `## Hard Rules`), not on inline step-local MUST/NEVER markers (those appropriately co-locate with their step).

| Skill | Lines | Hard-Rules-class section? | Position | Verdict |
|---|---|---|---|---|
| `skills/review-skill/SKILL.md` | 361 | `## Hard Rules` at line 354 | 354/361 = 0.98 → last 20% | PASS |
| `skills/audit-repo/SKILL.md` | 430 | None | — | NA (no trigger) |
| `skills/scaffold-skill/SKILL.md` | 284 | None | — | NA (no trigger) |

**Result**: All three sampled skills pass CE-CP under the refined Hard-Rules-section predicate. The original step-local MUST hits (e.g., `b.5 must not begin until b.4 done` at review-skill line 149) are sequencing constraints inside numbered steps — appropriately co-located with their step, not cross-cutting Hard Rules subject to LiM placement concerns. New item is preventive going forward; future skills introducing a `Hard Rules` section in the middle 60% of a ≥150-line body will be flagged.

## Cross-Validation Posture

- Liu et al. (TACL 2024, peer-reviewed) — primary
- Zhang et al. arXiv:2403.04797 — independent corroboration
- ACL 2024 Findings (arXiv:2406.16008) — independent calibration approach

All Tier-1, peer-reviewed or in major venues. Passes web-research rule.

## Pre-Existing Repo Coverage

The baseline section §"Context Placement" (line 79 of `engineering-baseline.md`) already cited Liu et al.'s LiM effect informally:

> **Context Placement** `[Proven result]` — Place critical instructions at START and END, never only in the middle. LiM effect peaks at <50% context utilization; at >50%, weight toward END. Reduced in larger models. Check: are key instructions anchored at both ends?

This research file consolidates the evidence with full citations and adds the operationalized CE-CP rubric item the baseline guidance previously lacked.

## References

- arXiv:2307.03172 — Liu et al., Lost in the Middle (TACL 2024)
- arXiv:2403.04797 — Zhang et al., Found in the Middle / Ms-PoE
- arXiv:2406.16008 — Found in the Middle: Calibrating Positional Attention Bias (ACL 2024 Findings)
- arXiv:2406.17095 — Attention Instruction
- https://aclanthology.org/2024.tacl-1.9/ — TACL canonical
- https://github.com/nelson-liu/lost-in-the-middle — code+data

## Repo Cross-References

- `skills/review-claude-config/references/engineering-baseline.md` §"Context Placement" — pre-existing baseline citation
- `research/context-engineering/anthropic-effective-context-engineering.md` — Anthropic guidance on context-budget
- `skills/review-claude-config/references/scoring-rubric.md` §"Observation-Masking Parity" — adjacent CE binary section where CE-CP joins
