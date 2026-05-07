---
name: description-design-problem
description: Description Routing Trilemma — 5-role optimization for LLM-callable primitives (MCP tool, skill, agent, rule), with Saavedra DQ-1..DQ-6 rubric anchors.
last_refreshed: 2026-05-07
---

# Description Design Problem

Every LLM-callable primitive (MCP tool, skill, agent, rule) carries a `description` driving routing, execution priors, catalog economy, position-robustness, and catalog-graph coherence. Optima conflict; description-quality optimization alone is insufficient — protocol-level fixes (namespacing, resource specs) required alongside.

Class: P=`[Proven result]`, E=`[Engineering guidance]`, L=`[Low-evidence area]`, R=`[Repo default]`.

## 5-Role Trilemma

- **Routing-Trigger** `[E]` — concrete trigger + pushy framing (Anthropic; Saavedra DQ-1)
- **Execution-Prior** `[E]` — description ↔ in-execution behavior (Saavedra DQ-2/3)
- **Catalog-Economy** `[E]` — minimum tokens preserving other axes (Saavedra DQ-5; LongFuncEval)
- **Position-Robustness** `[R]` — discriminative mid-prompt
- **Catalog-Graph-Coherence** `[R]` — minimize inter-primitive collisions (Microsoft 775)

Trade-offs: Catalog-Economy compresses against the other four; Routing-Trigger pushiness collides with Catalog-Graph-Coherence.

## Saavedra 6-Component Rubric

Likert-5; smell <3. Paper: DQ-4=Parameter Explanation, DQ-5=Length and Completeness.

- **DQ-1 Purpose** — what it does
- **DQ-2 Guidelines** — how/when to use
- **DQ-3 Limitations** — when NOT to use
- **DQ-4 Parameters** — inputs explained
- **DQ-5 Length** — concise + complete
- **DQ-6 Examples** — usage examples

Baseline (Saavedra arXiv 2602.14878; n=856, 103 servers, ICC 0.76–0.90):

- 97.1% of tool descriptions exhibit ≥1 smell `[Proven result]`
- +5.85pp augmentation effect across 6 components `[Proven result]`

## Per-Primitive Applicability

Saavedra empirical scope: MCP-Tool only.

| Component | MCP-Tool | Skill | Agent | Rule |
|-----------|----------|-------|-------|------|
| DQ-1 Purpose | ✓ P | ✓ E | ✓ E | ✓ R |
| DQ-2 Guidelines | ✓ P | ◐ L | ✓ E | ✓ R |
| DQ-3 Limitations | ✓ P | ◐ L | ✓ E | ✓ R |
| DQ-4 Parameters | ✓ P | ◐ L | ◐ L | N/A |
| DQ-5 Length | ✓ P | ✓ E | ✓ E | N/A |
| DQ-6 Examples | ✓ P | ◐ L | ◐ L | N/A |

✓=applies, ◐=weak evidence, N/A=not meaningful.

## Anti-Patterns

1. **Vague routing predicate** — "as needed" / "if appropriate"; fails DQ-1.
2. **Snapshot-name-only description** — body restates filename; fails DQ-1.
3. **Missing Limitations** — no out-of-scope clause; over-triggers; fails DQ-3.
4. **Catalog flooding** — overlapping vocabulary; LongFuncEval up to 85% drop `[Proven result]`.

## Sources

- Saavedra et al. (2026) — *MCP Tool Descriptions Are Smelly!* — https://arxiv.org/html/2602.14878v1
- Kate et al. (2025) — *LongFuncEval* — https://arxiv.org/abs/2505.10570
- Microsoft Research — *Tool-Space Interference in the MCP Era* — https://www.microsoft.com/en-us/research/blog/tool-space-interference-in-the-mcp-era-designing-for-agent-compatibility-at-scale/
- Anthropic Skill Creator — https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md
