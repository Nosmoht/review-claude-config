---
last_refreshed: 2026-04-19
---

# Rubric Calibration Evidence for Issues #4, #5, #6, #10, #62

Evidence-backed operationalization for P0.5 rubric changes. Each issue gets concrete binary-verifiable checklist items with BOUNDARY PASS/FAIL examples and cited Tier-1 sources. Feeds `skills/review-claude-config/references/scoring-rubric.md` and `engineering-baseline.md` updates.

## TL;DR

- **#4 Trigger-consistency (Metadata B/C)**: 4 binary items (META-1a, META-1b, META-2, META-3a, META-3b). Evidence: 61.8 % performance drop on semantically-equivalent description rephrasings (arXiv:2602.16666).
- **#5 Observation-masking parity (CE Grade-A)**: CE-X binary item with decision table. Evidence: 52 % cost reduction with solve-rate parity on SWE-bench Verified (arXiv:2508.21433).
- **#6 Verification criteria (Completeness A)**: COMP-X, COMP-Y, COMP-Z binary items. Evidence: RubricEval (arXiv:2603.25133), RULERS (arXiv:2601.08654 — QWK 0.73 vs 0.26 without evidence-cap), CheckEval (+0.45 agreement), IFEval (perfect κ on programmatic verifiability), MAST FC3 cluster.
- **#10 Task-type rubric variants (CE + GA)**: documentation-only override tables via `task-type-rubric-variants.md` + hybrid resolution algorithm. Evidence: AdaRubric (arXiv:2603.21362, r=0.79 vs r=0.63 fixed rubric).
- **#62 Third-person description (Metadata B/C)**: META-4 binary item caps Metadata at C when description uses first-person or second-person imperative. Evidence: Anthropic Skills best-practices Warning block — "Always write in third person… inconsistent point-of-view can cause discovery problems." Originally-proposed META-5 (ban `hooks` in plugin.json) dropped after Tier-1 contradiction with plugins-reference.

All items follow the canonical template: `<ID> <Label>: <observable>. PASS: <example>. FAIL: <example>. Verification: <regex|glob|count|LLM-binary>.`

## Issue #4 — Metadata Trigger-Consistency (B/C discriminator)

### Problem

Description-body trigger drift is a leading cause of skill misdispatch. LLMs re-route based on the description alone; when the body triggers on conditions not mentioned in the description, activation fails silently.

### Checklist Items

**META-1a Trigger-Match-Primary**
- Observable: description contains the body's primary trigger keyword (regex substring).
- PASS: "Use when reviewing MCP server configs" + body triggers on `.mcp.json`.
- FAIL: body triggers on `.mcp.json` but description says "Use for configurations".
- Verification: regex match of body trigger keyword in description field.

**META-1b Trigger-Match-Generalization** (OR-joined with META-1a)
- Observable: description uses `when|for|during|upon` followed by a domain term that covers the body triggers.
- PASS: "Use for any MCP manifest" (covers `.mcp.json`, `mcp-servers.json`).
- FAIL: vague scope without domain anchor.
- Verification: regex match against `/\b(when|for|during|upon)\s+\S+/i`.

**META-2 Anti-Pattern Example**
- Observable: description contains at least one negative-case phrase.
- PASS: "Do NOT use for agents or rules — use /review-agent instead."
- FAIL: "Use this skill when you need to review a skill." (positive example only)
- Verification: regex `/do ?not use|not for|skip (when|if)/i`.

**META-3a Concrete Trigger**
- Observable: no vague trigger language.
- PASS: "when file contains hooks.json".
- FAIL: "use as appropriate", "if useful", "when needed".
- Verification: regex exclusion `/as needed|if appropriate|when useful/i`.

**META-3b Sibling-Distinguishability**
- Observable: no sibling SKILL.md in the same plugin shares ≥2 trigger-keywords.
- Verification: glob siblings, tokenize descriptions, compute trigger-keyword overlap.

### Grade Boundary

| Grade | Condition |
|-------|-----------|
| A | all META items pass + no sibling overlap |
| B | all META items pass |
| C | META-2 fails (no negative example) OR META-3 ambiguities |
| D/F | META-1 fails (fundamental dispatch failure) |

### Evidence

- [arXiv:2602.16666 — AI Agent Reliability](https://arxiv.org/abs/2602.16666) — R_prompt metric: 61.8 % performance drop on semantically-equivalent rephrasings. **Tier 1**.
- [Anthropic Skill Creator Blog 2026-01](https://www.anthropic.com/engineering) — optimized descriptions raise activation from ~20 % to ~90 %. **Tier 2**.

## Issue #5 — Observation Masking Parity (CE Grade-A)

### Problem

Current rubric implicitly rewards LLM-based context summarization as a Grade-A strategy. Recent evidence shows simple observation masking (dropping older tool outputs without any LLM call) achieves the same or better task performance at ~50 % of the cost. Over-engineering with mandatory summarization is an anti-pattern.

### Checklist Item

**CE-X Compaction-Strategy Declaration**
- Observable: if the workflow keeps conversation history ≥10 turns AND uses LLM-based summarization, the skill body contains ≥1 sentence justifying why masking is insufficient.
- PASS: "Rotating window: dropping entries older than 20 tool-calls." (masking declared)
- PASS: "Summarize every 10 turns because semantic condensation is required — masking would lose dependency-graph signal." (summarization with justification)
- FAIL: "Summarize prior conversation every 10 turns via LLM call." (summarization without justification → over-engineering penalty)
- Verification: LLM-binary check on skill body.

### Decision Table (for `engineering-baseline.md` §Observation Masking)

| Context | Recommendation |
|---------|----------------|
| Output <1 K tokens AND turn-history ≤5 | Neither masking nor summarization needed |
| Output ≥1 K tokens AND non-decision-relevant for later turns | Masking preferred |
| Output ≥1 K tokens AND semantic condensation required | Summarization justified |

Grade-A only when the skill explicitly acknowledges one of these three regimes.

### Evidence

- [arXiv:2508.21433 — The Complexity Trap](https://arxiv.org/abs/2508.21433) (NeurIPS 2025 DL4Code) — masking achieves 52 % cost reduction with solve-rate parity on SWE-bench Verified, 5 models. **Tier 1**.
- [arXiv:2307.03172 — Lost in the Middle](https://arxiv.org/abs/2307.03172) (TACL 2024) — RoPE attention decay; long contexts lose ~30 % accuracy when relevant info sits in the middle. **Tier 1**.

## Issue #6 — Verification Criteria (Completeness A-Criterion)

### Problem

Output format and verification are orthogonal. A skill that defines perfect output format but has no verification step can produce fluent-sounding wrong answers. Current rubric folds verification implicitly into Completeness without discriminating.

### Checklist Items

**COMP-X Success Criteria**
- Observable: explicit success condition defined, not just output format.
- PASS: "Complete when all sub-tasks report `status: ok`."
- FAIL: "Produce JSON with fields X, Y, Z." (format only, no success criterion)
- Verification: regex `/complete when|success when|done when|finished when/i` in skill body.

**COMP-Y Verification Method**
- Observable: programmatic check or explicit binary LLM item, not holistic "looks good".
- PASS: "Verification: `jq '.status == \"ok\"'` returns true AND all fields non-null."
- FAIL: "Verify the output looks correct and is well-formatted."
- Verification: regex exclusion `/looks good|seems correct|appears valid|well[- ]formatted/i`; inclusion preference for concrete verbs (`parses`, `returns`, `equals`, `matches`).

**COMP-Z Evidence Trail**
- Observable: verification-decision evidence recorded (not silent pass/fail).
- PASS: Output spec includes `verification: [regex match, path cited, file state]`.
- FAIL: Output spec has no verification-log field.
- Verification: regex `/evidence|citation|quote|verified against|verification:/i` in output-spec section.

### Evidence

- [arXiv:2603.25133 — RubricEval](https://arxiv.org/abs/2603.25133) (Mar 2026) — Task Completion is a separate evaluation dimension, not a sub-item of Prompt Engineering. GPT-4o achieves only 55.97 % accuracy on "hard" rubric subset. **Tier 1**.
- [arXiv:2601.08654 — RULERS](https://arxiv.org/abs/2601.08654) (Jan 2026) — Evidence-cap mechanism: QWK 0.7276 with cap vs. 0.2643 without. **Tier 1**.
- [arXiv:2311.07911 — IFEval](https://arxiv.org/abs/2311.07911) (Nov 2023, ICLR 2024) — Programmatic verifiability → perfect inter-rater κ. **Tier 1**.
- [arXiv:2403.18771 — CheckEval](https://arxiv.org/abs/2403.18771) (EMNLP 2025) — Binary yes/no verification improves agreement by +0.45 across 12 evaluator models vs. Likert. **Tier 1**.
- arXiv:2503.13657 — MAST FC3 cluster: premature termination ~8 %, incomplete verification ~12 %, incorrect verification ~5 % of SWE-agent failures. Root cause: skills lacking explicit success conditions. **Tier 1**.

## Issue #10 — Task-Type Rubric Variants (CE + GA)

### Problem

A single fixed rubric penalizes intentionally-minimal designs and misevaluates specialized skills. CE criteria for an orchestrator skill differ fundamentally from CE criteria for a code-review skill. Fixed rubrics correlate ~r=0.63 with human judgment; task-adaptive rubrics reach r=0.79.

### Approach

Do not alter the core 7-dimension rubric. Instead, publish task-type override tables that adjust dimension weight or swap-in task-specific sub-criteria.

### Task-Type Override Tables (in companion file `task-type-rubric-variants.md`)

| Task type | Primary CE criterion | Primary GA criterion | Notes |
|-----------|---------------------|----------------------|-------|
| Agentic orchestrator | Subagent contract clarity, delegation scope, failure paths | Task decomposition accuracy, routing correctness | JIT retrieval irrelevant; focus on agent boundaries |
| Code review / analysis | Token density, minimal toolset, focused tooling | Domain expertise coverage (language + framework) | Intentionally small context is good; do not penalize |
| Research synthesis | JIT retrieval, source quality, citation management | Synthesis completeness, argument structure | Needs high tool diversity for sources |
| Scaffold / template | Output schema completeness, type safety | Template correctness, example variety | CE is secondary |
| Interactive tutoring | Progressive disclosure, error recovery, feedback quality | Pedagogical structure, misconception addressing | User-interaction loop is primary |

### Task-Type Resolution Algorithm (hybrid)

1. **Deterministic heuristics** (no LLM):
   - `allowed-tools` contains `Write+Bash` → scaffold OR orchestrator
   - `allowed-tools` contains `TaskCreate` → orchestrator
   - name prefix `review-|audit-|classify-` → code-review
   - name prefix `research-|sync-|refresh-` → research-synthesis
   - name prefix `scaffold-|develop-|apply-` → scaffold
2. **Reviewer override**: `/review-skill --task-type=<type>` CLI flag.
3. **Ambiguity** (2+ heuristics match): LLM chooses with single-sentence justification; choice logged to report certificate.

### Evidence

- [arXiv:2603.21362 — AdaRubric](https://arxiv.org/abs/2603.21362) (Mar 2026) — Task-adaptive rubrics: Pearson r=0.79 with humans vs. r=0.63 fixed. Krippendorff α=0.83 (deployment-grade). DPO-trained agents +6.8 to +8.5 pp task success vs. Prometheus baseline. SWE-bench unseen domains +4.9 pp. **Tier 1**.
- arXiv:2603.25133 — RubricEval: "Format Structure, Task Completion, Role/Persona are the three hardest rubric categories for LLM judges." **Tier 1**.

## Issue #62 — Metadata Third-Person Description (META-4)

### Problem

Skill and agent frontmatter `description` fields written in first person ("I help you…") or second person ("You can use this to…") cause discovery problems. The description is injected into the system prompt alongside descriptions from 100+ other skills; inconsistent point-of-view across the pool confuses the dispatcher and reduces activation precision.

### Checklist Item

**META-4 Third-Person Description**
- Observable: `description` frontmatter field contains no first-person pronouns (`I`, `my`, `me`) and no second-person imperative (`you can`, `your`).
- PASS: "Evaluates MCP server configs and produces a quality certificate."
- FAIL: "I help you review your MCP configs."
- Verification: regex exclusion on description field — `\bI\s` (case-sensitive), `\bmy\s`, `\bme\s`, `\byou can\s`, `\byour\s` (case-insensitive). Any match → FAIL.

### Grade Boundary

| Grade | Condition |
|-------|-----------|
| B or higher | META-4 ✓ (third person throughout) |
| C | META-4 ✗ (any first-person or second-person imperative anti-pattern) |

META-4 is a C-cap, not D/F: the description is still parseable and the skill still dispatches; discovery precision is degraded but not broken. Contrast with META-1 (missing trigger keyword → D/F dispatch failure).

### Evidence

- **Anthropic Skills best-practices** (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices, fetched 2026-04-20) — **Warning block**: "Always write in third person. The description is injected into the system prompt, and inconsistent point-of-view can cause discovery problems." Good example: "Processes Excel files and generates reports." Anti-patterns called out verbatim: "I can help you process Excel files" and "You can use this to process Excel files." **Tier 1** (official vendor doc).

### Non-change: META-5 dropped

The originally-proposed META-5 (ban `hooks` key in `.claude-plugin/plugin.json`) contradicts the official Anthropic plugins-reference (https://code.claude.com/docs/en/plugins-reference, fetched 2026-04-20) which lists `hooks` as a valid top-level manifest field (`string | array | object`) with an inline-hooks example. A check banning `hooks` would false-positive on spec-compliant plugins. See #62 comment thread for full contradiction.

## Canonical Item Template (applied to all items above)

```
<ID> <Short-Label>: <single observable in present tense>.
BOUNDARY PASS: <≤15-word example>.
BOUNDARY FAIL: <≤15-word example>.
Verification: <regex|glob|count|LLM-binary> <exact check>.
```

This template is mandatory for new rubric items added via P0.5. Non-binary items (Likert-scale) are explicitly rejected — they correlate poorly with human judgment.

## Sources (consolidated)

Tier 1:
- [arXiv:2602.16666 — AI Agent Reliability](https://arxiv.org/abs/2602.16666)
- [arXiv:2508.21433 — The Complexity Trap](https://arxiv.org/abs/2508.21433)
- [arXiv:2307.03172 — Lost in the Middle](https://arxiv.org/abs/2307.03172)
- [arXiv:2603.25133 — RubricEval](https://arxiv.org/abs/2603.25133)
- [arXiv:2601.08654 — RULERS](https://arxiv.org/abs/2601.08654)
- [arXiv:2311.07911 — IFEval](https://arxiv.org/abs/2311.07911)
- [arXiv:2403.18771 — CheckEval](https://arxiv.org/abs/2403.18771)
- [arXiv:2603.21362 — AdaRubric](https://arxiv.org/abs/2603.21362)
- arXiv:2503.13657 — MAST

Tier 2:
- Anthropic Skill Creator Blog, Jan 2026
- Local research: `research/rubric-design/rubric-design-for-llm-evaluators.md`, `research/checklist-calibration/checklist-calibration.md`, `research/verification-methods/verification-methods-per-dimension.md`
