---
last_refreshed: 2026-04-28
---

# Rubric Calibration Evidence for Issues #4, #5, #6, #10, #29, #62, #64, #66

Evidence-backed operationalization for P0.5 rubric changes. Each issue gets concrete binary-verifiable checklist items with BOUNDARY PASS/FAIL examples and cited Tier-1 sources. Feeds `skills/review-claude-config/references/scoring-rubric.md` and `engineering-baseline.md` updates.

## TL;DR

- **#4 Trigger-consistency (Metadata B/C)**: 4 binary items (META-1a, META-1b, META-2, META-3a, META-3b). Evidence: 61.8 % performance drop on semantically-equivalent description rephrasings (arXiv:2602.16666).
- **#5 Observation-masking parity (CE Grade-A)**: CE-X binary item with decision table. Evidence: 52 % cost reduction with solve-rate parity on SWE-bench Verified (arXiv:2508.21433).
- **#6 Verification criteria (Completeness A)**: COMP-X, COMP-Y, COMP-Z binary items. Evidence: RubricEval (arXiv:2603.25133), RULERS (arXiv:2601.08654 — QWK 0.73 vs 0.26 without evidence-cap), CheckEval (+0.45 agreement), IFEval (perfect κ on programmatic verifiability), MAST FC3 cluster.
- **#10 Task-type rubric variants (CE + GA)**: documentation-only override tables via `task-type-rubric-variants.md` + hybrid resolution algorithm. Evidence: AdaRubric (arXiv:2603.21362, r=0.79 vs r=0.63 fixed rubric).
- **#62 Third-person description (Metadata B/C)**: META-4 binary item caps Metadata at C when description uses first-person or second-person imperative. Evidence: Anthropic Skills best-practices Warning block — "Always write in third person… inconsistent point-of-view can cause discovery problems." Originally-proposed META-5 (ban `hooks` in plugin.json) dropped after Tier-1 contradiction with plugins-reference.
- **#66 Ambiguity markers (Clarity B/C)**: CLAR-1 (fuzzy quantifiers in step parameters) and CLAR-2 (unresolved pronouns referring to prior tool outputs) both cap Clarity at C. Evidence: ambiguity taxonomy F1=0.83 on Gemma 3 12B (arXiv:2507.11525, ROMAN 2025); 61.8 % accuracy drop on subtle constraint-wording nuances (arXiv:2512.14754, ACL 2026).
- **#64 Termination criteria (Completeness A)**: COMP-W binary item requires iterative skills/agents to declare an explicit termination predicate distinct from COMP-X success. Evidence: MAST task-verification-and-termination failure cluster (arXiv:2503.13657); Meltdown Onset Point reliability framework (arXiv:2603.29231, 2026-03-31); AgentDebug +24 % all-correct accuracy from failure annotation (arXiv:2509.25370, 2025-09). Grade-A schema-compliance clarification deferred — requires direct verification of MCP 2025-11-25 spec.
- **#65 Goal-Alignment Checkpoint-Decomposition (A-ceiling / C-floor)**: GA-X LLM-binary item — A requires explicit domain-expert checkpoints detectable without run; C-floor caps Goal Alignment at C when goal-surface is met but ≥1 checkpoint is missing. Evidence class: Engineering guidance. Tier-1 sources: arXiv:2512.12791v2 (Scenario S1: 100%/33% surface/policy gap); arXiv:2601.15153 (+206%). Gaia2/ARE ICLR 2026 corroborates frontier task-completion ceiling.

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

## Issue #64 — Completeness Termination Criteria (COMP-W)

### Problem

The current Completeness binary items COMP-X (success criteria), COMP-Y (verification method), and COMP-Z (evidence trail) cover what a skill should produce and how to validate it — but none of them requires an explicit termination condition for iterative or looped workflows. MAST (arXiv:2503.13657) identifies task-verification-and-termination as a distinct high-frequency failure cluster. Skills with loops but no stopping predicate drift into unbounded retry, silent incomplete runs, or Meltdown-Onset-Point-style cascading failure (arXiv:2603.29231).

### Checklist Item

**COMP-W Termination Criteria**
- Observable: skills/agents whose body contains iterative language (`for each`, `retry`, `iterate`, `while`, `until`, `loop`) declare an explicit termination predicate distinct from the COMP-X success condition.
- PASS (iterative with predicate): "retry up to 3 times on HTTP 503; escalate after 3 consecutive failures."
- PASS (non-iterative): skill is one-shot (no loop language present) — COMP-W not applicable.
- FAIL (iterative, no predicate): "retry on failure" without a max-attempt count or escalation path.
- Verification: two-step — (1) detect loop language with regex `/for each|retry|iterate|while|until\s|loop/i`; (2) when detected, require a termination-predicate match `/stop when|terminate|halt|max.*iterations?|escalate after|loop until|exit (if|when)|stopping condition/i`.

### Grade Boundary

| Grade | Condition |
|-------|-----------|
| A | COMP-W ✓ AND COMP-X ✓ AND COMP-Y ✓ AND COMP-Z ✓ |
| B | COMP-W ✓ and one of COMP-X/Y/Z implicit but recoverable |
| C | COMP-W ✗ (iterative workflow without termination predicate) |

COMP-W is a C-cap (not D/F) — a skill with a loop and no stop condition still executes, but risks unbounded runtime or silent truncation. Contrast with COMP-X (missing success criterion = cannot verify completion at all).

### Evidence

- [arXiv:2503.13657 — Why Multi-Agent LLM Systems Fail](https://arxiv.org/abs/2503.13657) (Cemri et al., 2025-03) — 14 MAST failure modes identified via 1600+ annotated traces; task-verification-and-termination cluster ~15 % of SWE-agent failures. **Tier 1**.
- [arXiv:2603.29231 — Beyond pass@1: Reliability Science Framework](https://arxiv.org/abs/2603.29231) (Khanal, Tao, Zhou, 2026-03-31) — Reliability Decay Curve, Variance Amplification Factor, Graceful Degradation Score, Meltdown Onset Point (MOP); frontier models exhibit up to 19 % meltdown rate on long-horizon tasks. Motivates explicit termination as a reliability discipline. **Tier 1**.
- [arXiv:2509.25370 — Where LLM Agents Fail and How They can Learn From Failures](https://arxiv.org/abs/2509.25370) (Zhu et al., 2025-09-29) — AgentErrorTaxonomy + AgentErrorBench + AgentDebug framework; +24 % all-correct accuracy, +17 % step accuracy via failure annotation. Validates annotation-grade termination predicates as a lever for agent reliability. **Tier 1**.

### Non-change: Grade-A schema-compliance refinement deferred

Issue #64 also proposed refining the Completeness Grade-A wording from "output format defined" to "schema-compliant output spec" for agents producing structured output (citing MCP 2025-11-25 mandate). This refinement is deferred: the issue itself classifies the MCP citation as Tier 2 and requests direct verification against https://spec.modelcontextprotocol.io before adoption. Split into a follow-up sub-issue once spec-direct verification is complete.

## Issue #66 — Clarity Ambiguity Markers (CLAR-1 / CLAR-2)

### Problem

The current Clarity C-test in `scoring-rubric.md:19` covers one ambiguity class — bare vague predicates ("if needed", "as appropriate") without a concrete trigger. 2026 NL-instruction ambiguity research identifies two additional binary-verifiable markers with comparable or higher discriminative value:

1. **Fuzzy quantifiers** in step parameters (`slightly`, `a bit`, `some`, `roughly`) — turn a deterministic parameter into a free-floating value the agent must interpret at runtime.
2. **Unresolved pronouns** referring to prior tool outputs (`it`, `them`, `that`, `this`) without an adjacent noun phrase — force the agent to guess which previous output is the antecedent when multiple candidates exist.

Both markers correspond to the `WS-2 Clarity` divergence identified as the largest driver of the P1.1 multi-perspective pilot-convergence FAIL (see #68). Adding them as binary-verifiable items reduces reviewer divergence on Clarity grading.

### Checklist Items

**CLAR-1 Fuzzy-Quantifier-Free**
- Observable: step parameters and instructions contain no fuzzy quantifier.
- PASS: "fetch 10 entries", "reduce the window by 2 turns", "retry 3 times".
- FAIL: "fetch roughly 10 entries", "slightly reduce the window", "retry some times".
- Verification: regex exclusion on instruction body — `/\b(slightly|a bit|roughly|somewhat)\b/i` and context-aware `\bsome\b` (excluding placeholder paths like `research/some/file.md` and rubric meta-text describing grade states).

**CLAR-2 Resolved-Pronoun**
- Observable: every pronoun referring to a prior tool output has an explicit antecedent in the same step or the immediately preceding step.
- PASS: "parse the grep output; store the matches in results.json."
- FAIL: "parse the output; then process them." (ambiguous antecedent across tool calls)
- Verification: LLM-binary check scoped to instruction pronouns (`it`, `them`, `that`, `this`, `those`) appearing without an adjacent noun phrase.

### Grade Boundary

| Grade | Condition |
|-------|-----------|
| B or higher | CLAR-1 ✓ AND CLAR-2 ✓ |
| C | CLAR-1 ✗ OR CLAR-2 ✗ (ambiguity → interpretation required) |

CLAR-* failures are C-caps, not D/F: the workflow is still followable, but step-parameter ambiguity or unresolved antecedents make the execution non-deterministic. Contrast with bare vague predicates in the original C-test, which are likewise C-caps.

### Evidence

- [arXiv:2507.11525 — LLM-based ambiguity detection](https://arxiv.org/abs/2507.11525) (Davila et al., ROMAN 2025, 2025-07-15) — operational ambiguity taxonomy across linguistic, contextual, procedural, and critical classes. F1=0.83 with Gemma 3 12B ensemble. High-ambiguity markers identified: unresolved pronouns, fuzzy spatial/temporal hedges ("slightly", "move more left"), missing procedural parameters, implicit assumptions. **Tier 1**.
- [arXiv:2512.14754 — Revisiting the Reliability of Language Models in Instruction-Following](https://arxiv.org/abs/2512.14754) (Dong et al., ACL 2026, submitted 2025-12-15, revised 2026-04-14) — IFEval++ benchmark with `reliable@k` metric. Subtle constraint-wording nuances cause up to 61.8 % accuracy drop on small models. Tested across 20 proprietary + 26 open-source LLMs. **Tier 1**.
- Industrial confirmation: prompt-determinism case study ([ScienceDirect S2666827025001872](https://www.sciencedirect.com/science/article/pii/S2666827025001872), 2025) — prompt structure outweighs model choice for determinism. **Tier 2**.

### Non-change: none

No items dropped. CLAR-1 and CLAR-2 are both directly supported by the Tier-1 sources above; no contradiction with Anthropic docs or other rubric items was surfaced during research.

## Issue #61 — Safety MCP Tool-Poisoning + OWASP ASI Extensions

### Problem

2026 Q2 MCP-security research exposed three gap classes in the Safety rubric before commit 14d3fe0: (1) no MCP-source-integrity requirement for Grade A, letting skills consume unpinned tool descriptions without grade impact; (2) no Tier-0 same-turn combination class for untrusted-input + high-risk-tool without sanitization; (3) agentic overlay covered only R1–R10 and missed the OWASP ASI09 rubber-stamp-HITL surface and ASI08 cascading-failure containment for deep delegation chains. `R9` also understated persistent memory-write scope (ASI06).

### Rubric Changes (landed in `scoring-rubric.md:53-62` and `tool-grant-decision-tree.md:22-29`)

1. **MCP source integrity (Grade A clause + C cap)** — A requires "MCP tools consumed only from pinned / integrity-verified / allowlisted sources"; unpinned/unverified MCP consumption caps Safety at C.
2. **R4b HITL-surface resistance** — agentic High check added: approval-prompt text is composed from fixed templates or constrained options, not free-form model output derived from tool results or external content. Maps to ASI09.
3. **R11 Cascading containment** — agentic High check added for delegation chains of depth ≥3: circuit breaker OR rollback semantics OR blast-radius limit must be declared. Maps to ASI08.
4. **R9 memory-write scope** — existing High check extended: Safety/PII/credential scope AND persistent-memory-write scope. Maps to ASI06.
5. **Tier-0 same-turn combination (Safety F)** — `tool-grant-decision-tree.md` adds Tier-0 forbidden class: untrusted external content (WebFetch/WebSearch/MCP output/raw `$ARGUMENTS`) + high-risk tool (Bash/Write/Edit/MCP write) in the same turn without validation/approval gate → Safety F. Maps to ASI02.

### Grade Boundary

| Change | Condition | Grade impact |
|---|---|---|
| MCP source integrity | all MCP-consuming skills specify pinning / integrity check / allowlist | A-eligible |
| MCP source integrity | unpinned/unverified MCP consumption | Safety cap at C |
| R4b | HITL-heavy skill uses fixed-template/constrained-option approval prompts | B-retention |
| R4b | HITL approval text synthesized from untrusted content | Safety cap at C (High check missing) |
| R11 | delegation depth ≥3 declares circuit breaker / rollback / blast-radius limit | B-retention |
| R11 | depth-≥3 chain with no containment primitive | Safety cap at C |
| R9 memory | persistent-memory-write scope explicitly addressed alongside PII/cred scope | B-retention |
| R9 memory | memory-write surface unaddressed | one-grade shift per missing High check |
| Tier-0 | untrusted-input + high-risk-tool + sanitization/approval gate present | A/B per base grade |
| Tier-0 | unsanitized same-turn combination | Safety F (hard floor) |

Caps compose multiplicatively: a skill missing both R4b and R11 on an agentic pipeline is capped at C (two High checks missing = two-grade shift from A = C under the `agentic overlay` grade mapping).

### BOUNDARY PASS/FAIL exemplars

**MCP-1 MCP-Source-Integrity**
- Observable: every MCP server referenced in `mcpServers` frontmatter or body is paired with a pinning/integrity/allowlist statement within the same file.
- PASS: `"mcpServers: [{name: 'stripe', url: 'https://mcp.stripe.com', sha256: 'a1b2...', allowlist_tools: ['create_invoice', 'list_customers']}]"`.
- FAIL (boundary): `"mcpServers: ['filesystem', 'github']"` — named but no version pin, no integrity attestation, no tool allowlist.
- FAIL (egregious): body calls `mcp__arbitrary_server__*` with no `mcpServers` declaration at all.
- Verification: regex — for each `mcp__<server>__` reference in body OR each entry in `mcpServers` frontmatter, require ≥1 match within the same file of `/(pinned|sha256|sha-256|version\s*[:=]|revision\s*[:=]|integrity|allowlist|allowed\s+tools|trusted\s+source|signed)/i`. Source: MCPTox arXiv:2508.14925 (2025-08) — 72.8 % tool-poisoning attack success on o1-mini, 70.2 % on Phi-4 across 45 servers / 353 tools / 1,312 cases when source integrity is not gated.

**R4b HITL-Surface-Resistance**
- Observable: every AskUserQuestion/confirmation/approval prompt is composed from either a hardcoded template string OR an enum of fixed options — not interpolated from tool outputs, `$ARGUMENTS`, MCP responses, or WebFetch content.
- PASS: `"AskUserQuestion('Delete the file at {validated_path}?', options=['Yes','No'])"` — path is validated (`MCP-1`-style) before interpolation, prompt text is fixed.
- FAIL (boundary): `"AskUserQuestion(f'Proceed with {tool_output.action_description}?', ...)"` — prompt text carries free-form model/tool output that the agent can craft to rubber-stamp.
- FAIL (egregious): no confirmation step at all on a destructive agentic path (separate R4 FAIL, not R4b).
- Verification: regex on approval-prompt construction — detect `/(AskUserQuestion|confirm|approve|prompt)/` within 400 chars of `/(f"|f'|\${|\.format\(|\+\s*[a-z_]+|str\()/` where the interpolated variable is NOT inside a whitelist of pre-validated identifiers (e.g., `path_validated`, `allowlisted_name`). Source: OWASP Top 10 for Agentic Applications 2026 **ASI09** Human-Agent Trust Exploitation — "rubber-stamp attack surface" where model-crafted approval text exploits habitual user trust.

**R11 Cascading-Containment**
- Observable: for agents declaring `Agent` or `Task` tools where the body indicates ≥3 levels of delegation (root → child → grandchild), the file contains at least one of: (a) circuit-breaker token (`circuit.breaker`, `open.*after.*failed`, half-open state), (b) rollback/compensating-action token, (c) numeric blast-radius limit (max downstream writes/invocations per root).
- PASS: `"If any grandchild times out 3 times in a rolling 100-invocation window, open the circuit breaker on that sub-agent for 60 s."`
- PASS (rollback): `"On grandchild failure, revert the parent's draft state before the dispatch; re-queue under human review."`
- FAIL (boundary): chain of `Agent → Agent → Agent` with only `maxTurns: 20` on each — per-agent cap but no cross-level containment.
- FAIL (egregious): unbounded delegation depth with no per-chain budget, no circuit breaker, no rollback.
- Verification: two-step — (1) detect chain depth ≥3 via count of Agent/Task dispatches transitively reachable from the body; (2) require ≥1 match of `/(circuit\s*breaker|rolling\s*window|open.*after\s+\d+|half[-\s]?open|rollback|compensating|revert|blast.radius|max\s+(downstream|child|descendant)\s+(writes?|invocations?|calls?))/i`. Source: OWASP Top 10 for Agentic Applications 2026 **ASI08** Cascading Failures; `research/autonomous-agent-reliability/autonomous-agent-reliability.md:362-365` citing the circuit-breaker three-state pattern (closed/open/half-open, typical 50 % failure threshold of last 100 requests).

**R9-memory Persistent-Memory-Write-Scope**
- Observable: skills/agents with `memory:` frontmatter (`user`/`project`/`local`) OR any `Write`-to-memory-path pattern include a scope rule naming what MAY be persisted, what MUST NOT be persisted, and a boundary predicate.
- PASS: `"Memory writes are project-scoped; credentials, secrets matching /[A-Za-z0-9_-]{20,}/, and user PII (email, phone) are stripped before persist. No user-scoped memory modifications."`
- FAIL (boundary): `"memory: project"` with no scope rule in the body — field declared, behavior undefined.
- FAIL (egregious): agent with `memory: user` that writes arbitrary tool output to memory without filtering.
- Verification: when `memory:` frontmatter is present OR body contains `Write` on a `memory/` path, require ≥1 match of `/(must not persist|do not (store|persist|write)|redact|strip|filter|scoped to|boundary predicate|only.*(projects?|session)|never.*credentials?|never.*PII)/i` within the file. Source: OWASP Top 10 for Agentic Applications 2026 **ASI06** Memory and Context Poisoning; `research/memory-poisoning/memory-poisoning-patterns.md` 3 poisoning vectors (instruction injection, stale accumulation, contradiction insertion).

**Tier-0 Same-Turn-Combination-Sanitized**
- Observable: when the body pairs a source of untrusted input (WebFetch/WebSearch/MCP output/`$ARGUMENTS`) with a high-risk tool (Bash/Write/Edit/MCP write) in the same sequential step, an intervening validation or approval gate is declared between them.
- PASS: `"Fetch the URL; validate response body matches the expected schema (Pydantic model); if valid, present AskUserQuestion preview before Write."`
- PASS (allowlist): `"MCP call returns a filename; assert filename matches /^[a-z0-9._-]+$/ AND is one of the 12 allowlisted reports; then Bash('cat ' + shell_quote(filename))."`
- FAIL (boundary): `"Fetch the URL; parse JSON; Bash('rm ' + json['filename'])."` — JSON parsed but filename is not validated before Bash consumes it.
- FAIL (egregious): `"Forward $ARGUMENTS directly to Bash."` — zero gate between untrusted input and shell.
- Verification: sequential-scan — for each adjacent pair `(source, sink)` where `source ∈ {WebFetch, WebSearch, MCP-output, raw $ARGUMENTS}` and `sink ∈ {Bash, Write, Edit, MCP-write}`, require an intervening match of `/(validate|schema|Pydantic|assert.*match|regex|allowlist|AskUserQuestion|preview|confirm|approval\s+gate|shell_quote|escape)/i` OR the source is transformed into a named validated variable before reaching the sink. Source: MCP Protocol Security arXiv:2601.17549 (2026) — 34-43 % command-injection rate across 2,614 MCP servers, 30+ CVEs Jan-Feb 2026 incl. CVSS 9.6 RCE; OWASP Top 10 for Agentic Applications 2026 **ASI02** Tool Misuse.

### Evidence

- [arXiv:2508.14925 — MCPTox](https://arxiv.org/abs/2508.14925) (2025-08) — 45 MCP servers, 353 tools, 1,312 attack cases; tool-poisoning attack success up to 72.8 % (o1-mini) and 70.2 % (Phi-4). Claude-3.7-Sonnet refusal rate <3 % — frontier-model alignment is insufficient; source integrity gating is the lever. **Tier 1**.
- [arXiv:2601.17549 — MCP Protocol Security](https://arxiv.org/html/2601.17549) (2026) — protocol-level defects amplify attack success by 23-41 %; 34-43 % command-injection rate measured across 2,614 MCP servers; 30+ CVEs Jan-Feb 2026 including CVSS 9.6 RCE. **Tier 1**.
- **OWASP Top 10 for Agentic Applications 2026** (ASI01–ASI10) — ASI02 Tool Misuse, ASI06 Memory/Context Poisoning, ASI08 Cascading Failures, ASI09 Human-Agent Trust Exploitation are the four new framework entries referenced by this issue. **Tier 1** (standards body).
- `research/autonomous-agent-reliability/autonomous-agent-reliability.md:319-327` (R4b) and `:362-368` (R11) — distilled wording for the agentic overlay checks. **Tier 1 derived**.
- `research/tool-least-privilege/tool-least-privilege-agents.md` — 5-tier high-risk tool combination checklist; Tier 0 forbidden class now codified in `tool-grant-decision-tree.md:22-29`.

### Non-change: OWASP 2026 PDF exact-wording verification deferred

The original issue Validation block requested fetching the OWASP Top 10 for Agentic Applications 2026 PDF for authoritative "Least-Agency" and "Strong Observability" phrasing before codifying. The rubric landed using paraphrased framework references (ASI02/06/08/09 mapped to rubric clauses); direct-quote verification is deferred until the PDF is reliably fetchable from a Tier-1 source. Split into a follow-up if verbatim wording alignment becomes a discriminator on real reviews.

### Non-change: `/run-eval-cases` regression deferred

Issue #61 Validation also requested `/run-eval-cases` against MCP skills and agentic chains. Only `docs/review-eval-cases.md` exists as the case inventory; no MCP-specific case is in the enumeration yet. A dedicated follow-up should add a case pair for (a) an MCP-consuming skill with pinned vs unpinned declaration, and (b) a depth-≥3 agent chain with and without containment primitive. Not a blocker for #61 close: the rubric is now operationally testable via real reviews (`/review-mcp-server`, `/review-agent`) on any MCP/agent artifact in the wild.

## Issue #65 — Goal-Alignment Checkpoint-Decomposition (A-ceiling / C-floor)

> Note: this file lives under `research/rubric-design/`, deliberately outside `scripts/validate_token_budgets.py` scan path (`skills/*/references/**/*.md`). Calibration evidence is research-class, not session-loaded; growth is bounded by editor discipline.

**Evidence class:** Engineering guidance (Tier-1 evidence anchors empirical surface/policy gap; clause wording is repo-internal distillation).

### Problem

Goal Alignment is the highest-weighted rubric dimension but has historically lacked a binary-verifiable boundary between A and C. Reviewers diverge on whether a skill that produces the stated artifact (goal-surface met) but skips domain-expert checkpoints — policy consultation, diagnostic pre-check, validation step — is A-eligible or C-capped. 2026 Tier-1 evidence shows the gap matters: agentic systems can achieve 100% tool-sequence correctness while only 33% policy adherence, exposing checkpoint-skip failures invisible to surface metrics.

### Checklist Item

**GA-X Checkpoint-Decomposition**

- **Observable:** workflow body declares explicit domain-expert checkpoints (policy consultation, diagnostic pre-check, validation step) such that omitting any checkpoint would be detectable by a reviewer without running the skill. A skill that achieves goal-surface (artifact produced, tool called) but omits ≥1 such checkpoint a practitioner rubric would require → C. The "practitioner rubric would require" qualifier is the **NA gate**: archetypes for which no domain-expert checkpoint is required (one-shot read-only transforms, simple formatters) are NA, not FAIL.

- **Category-specific evidence (anti-gameability).** Each named category requires substantive evidence, not just a label:
  - **policy consultation** → step references a specific path/file/document name (e.g., reads `tool-grant-decision-tree.md`, loads `references/*.md`, queries a spec). Not satisfied by an unsourced "consult policy" instruction.
  - **diagnostic pre-check** → step reads system state before mutation (e.g., RD-6 tool-availability probe pattern, file-existence check, glob conflict detection, schema-presence test). Not satisfied by a generic "check first" instruction.
  - **validation step** → step compares output to a schema/template/expected-shape (e.g., `report-template.md` schema check, sidecar applyability gate, parse-and-confirm of generated content). Not satisfied by `echo "validated"` or a no-op label.

- **BOUNDARY PASS (A-eligible):** "Apply skill workflow: (1) consult `tool-grant-decision-tree.md` policy, (2) run RD-6 tool-availability probe, (3) validate output against `report-template.md` schema, (4) emit certificate." Each checkpoint named, ordered, and reviewable with substantive evidence.

- **BOUNDARY FAIL (C-capped, missing all categories):** "Generate the review report and write it to `$CLAUDE_PLUGIN_DATA/reports/`." Goal-surface met (artifact produced) but no policy consultation, no diagnostic pre-check, no validation step named.

- **BOUNDARY FAIL (gameability — no-op label):** "(1) Generate the review report. (2) Validation step: `echo \"validated\"`. (3) Emit." Step labeled "Validation step" but body performs no domain validation. The category-specific evidence requirement (above) takes precedence over the literal label.

- **BOUNDARY FAIL (position — checkpoint after emission):** "(1) Write the report to disk. (2) Validation step: re-read the report and confirm it parses." Checkpoint named but executed AFTER goal-surface emission; cannot prevent a defective artifact from being persisted.

- **BOUNDARY NA (one-shot read-only transform, no Write/Bash/Edit):** A skill whose entire body is a single-step transformation with no policy gate, no state mutation, and no schema-validatable output (e.g., a plain text reformatter, a `.gitignore` lookup helper) — no checkpoint required by archetype. NA, not FAIL. The clause's "practitioner rubric would require" qualifier is the explicit NA gate.

- **Verification:** LLM-binary — for the workflow body, ask: "Does the skill name ≥1 of {policy consultation, diagnostic pre-check, validation step} as a distinct numbered/named step *before goal-surface emission*, with category-specific evidence (path-reference / state-read / schema-compare) rather than just a label?" Yes → PASS; No (and at least one was required by archetype) → FAIL; No (and none was required by archetype) → NA.

### Anti-double-counting with R4 / R4b / CLAR-3

GA-X PASS may not double-credit evidence already pinned to other agentic-overlay or clarity items. A skill that earns R4 PASS via a named escalation step OR CLAR-3 PASS via a named recovery target may NOT cite the SAME step as GA-X evidence. Reviewers must cite **distinct checkpoint evidence** for GA-X. This prevents the same workflow feature from triggering or excusing three separate caps.

### Grade Boundary

| Grade | Condition |
|-------|-----------|
| A     | All §A clauses pass AND GA-X ✓ (explicit checkpoints with category-specific evidence) |
| B     | §A partial; GA-X ✓ |
| C     | GA-X ✗ (goal-surface met but ≥1 archetype-required checkpoint missing) |
| —     | GA-X NA (archetype requires no domain-expert checkpoint; one-shot read-only transforms) |
| D/F   | inherit from §D/F base clauses |

GA-X is a C-cap (not D/F): the skill still produces the stated artifact, so goal achievement isn't zero — but practitioner-rubric-equivalence is broken. Contrast with §F (goal stated but body doesn't support achieving it = total failure).

### Perspective handling — standard advisory

GA-X is intentionally NOT registered in `scripts/merge_findings.py` `BINARY_CAPS` / `BINARY_ITEM_IDS` / `NARRATIVE_PARENT_IDS` and NOT added to `scripts/rubric_binary_evaluator.py`. Rationale:

1. **The §A/§C clause text is the test.** The perspective-correctness agent owns Goal Alignment (`merge_findings.py:348`) and applies the new clauses holistically when grading the dimension. A binary cap on top would double-fire.
2. **LLM-binary on free-form workflow text is unreliable for cap-firing.** Promoting to a deterministic cap (BINARY_CAPS) would produce false-positive C-caps on skills using non-canonical phrasing.
3. **GA-X follows the standard advisory pattern**, not a special path. Per `merge_findings.py:594-606`, ANY perspective finding whose `checklist_item` is not in BINARY_ITEM_IDS / NARRATIVE_PARENT_IDS is demoted to Low when `apply_caps=True`. GA-X behaves identically to all other unregistered narrative items — there is no GA-X-specific code path. The grade signal flows through the perspective-correctness agent's holistic Goal-Alignment grade BEFORE the merge demotion; demotion only suppresses the perspective's standalone finding emission, not the dim-grade signal.
4. **Fail-safe corner**: when `apply_caps=False`, demotion does not fire and GA-X may surface at perspective severity. This corner is reached when the binary-evaluator script is missing or crashed (per `merge-rules.md` §"Perspective Finding Handling" fail-safe path) — perspectives retain authority when binary infrastructure is unavailable, preventing silent under-reporting.

Future refinement (if a stable, repo-wide regex pattern emerges): promote GA-X to a binary item by adding `BINARY_CAPS.append(("GA-X", "Goal Alignment", "C"))`, `ITEM_DIMENSION["GA-X"] = "Goal Alignment"`, a `rubric_binary_evaluator.py` LLM-binary entry, plus matching `merge-rules.md` cap-table row and `agents/review-perspective-correctness.md` skip-list entry. Out of scope for #65.

**Future GA-* naming policy:** subsequent rubric-global GA items use the X/Y/Z suffix (e.g., GA-Y, GA-Z) to remain disjoint from per-archetype `GA-1`...`GA-5` namespaces in rule/claude-md/hook evaluation guides.

### Migration note for existing skills

Skills authored before #65 may need a single-line addition to retain A grades. The repo has converged on three convergent idioms; if your skill uses any of these, GA-X likely PASSes:

- **`scaffold-*`**: "Before presenting, run these validation checks against the generated content" (validation-step idiom).
- **`apply-*`**: "Step 2.4 Applyability gate" (validation-step idiom).
- **`review-*`**: "Completeness gate — success condition" (validation-step idiom) + Step 0/1 "Tool probe" + "Load References" (diagnostic + policy-consultation idioms).
- **`audit-*`**: typically pass via "Load Policy" / "Termination and Escalation" sections.
- **`one-shot transforms`**: usually NA (no archetype-required checkpoint).

A pre-merge full-repo `/review-skill` sweep is intentionally NOT performed (KV-cache reason). Post-commit, the 3 borderline cases identified by Round-3 backward-compat survey (`develop-hooks`, `audit-repo`, `audit-context-budget`) should be reviewed individually; if any falls to C, open per-skill follow-up issues — do not block #65 commit.

### Evidence

- [arXiv:2512.12791v2 — Beyond Task Completion](https://arxiv.org/abs/2512.12791) (2025-12-16) — assessment framework for agentic systems. **Verbatim finding (Table 3, Scenario S1 baseline — §4.1 "Cost Optimization (S1)"):** "S1 achieved perfect tool sequencing (100%) but only 33% policy adherence, indicating actions proceeded without consulting safety guidelines." Pillar-specific failure examples: "Skipped policy validation before instance termination"; "Missed diagnostic or verification steps before applying remediation." Demonstrates surface-correctness/policy-adherence gap. **Tier 1**.
  - **Note on terminology:** "checkpoint" is this rubric's editorial term; the paper uses "pillar-specific metrics" and "policy adherence" measures. The empirical 100/33 surface/policy gap is what the Tier-1 source supports — the term "checkpoint decomposition" is a repo-internal distillation of that gap into a reviewable rubric clause.
- [arXiv:2601.15153 — Codified Expert Domain Knowledge](https://arxiv.org/abs/2601.15153) (2026-01) — abstract reports **+206% improvement in output quality** with "expert-level ratings in all cases versus baseline's poor performance" via expert-rule augmentation (RAG + codified domain rules + visualization principles). Validates that codified domain checkpoints (not just retrieval) drive quality. **Tier 1**.
- [arXiv:2403.18771 — CheckEval](https://arxiv.org/abs/2403.18771) (EMNLP 2025) — Binary yes/no PASS/FAIL exemplars improve inter-evaluator agreement by +0.45 across 12 evaluator models vs holistic Likert. Justifies the BOUNDARY-pair format. **Tier 1**.

### Corroborating context (not load-bearing)

- [Gaia2 / ARE — Benchmarking LLM Agents on Dynamic and Asynchronous Environments](https://arxiv.org/abs/2602.11964) (ICLR 2026) — frontier agents cap at 42% pass@1 on real-world multi-step tasks (GPT-5 high best). The 42% ceiling is total task-failure rate from any cause, not specifically checkpoint-skip. Consistent with — but not direct evidence for — the surface/policy gap. Used here as ambient context that real-world multi-step task success is far from saturation.

### Non-change: weight constants

The 20%/25% Goal Alignment weight is unchanged.

### Non-change: Issue #32 (E8) is NOT operationalized — only complemented

Issue #32 enumerates four operational sub-tasks: (1) task extraction, (2) task→instruction coverage, (3) scope-creep check, (4) contradiction check. GA-X's predicate is **instruction→checkpoint-category presence** — fundamentally different from #32's task→instruction coverage. A skill could pass GA-X yet fail #32(2); or vice versa. #32 is closed with a **complementary-resolution comment** explicitly noting GA-X **does not** satisfy any of the four E8 sub-tasks; all four remain open follow-ups.

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
- [arXiv:2507.11525 — LLM-based Ambiguity Detection](https://arxiv.org/abs/2507.11525)
- [arXiv:2512.14754 — IFEval++ / reliable@k](https://arxiv.org/abs/2512.14754)
- [arXiv:2603.29231 — Beyond pass@1 Reliability Framework](https://arxiv.org/abs/2603.29231)
- [arXiv:2509.25370 — AgentErrorTaxonomy / AgentDebug](https://arxiv.org/abs/2509.25370)
- arXiv:2503.13657 — MAST
- [arXiv:2508.14925 — MCPTox](https://arxiv.org/abs/2508.14925)
- [arXiv:2601.17549 — MCP Protocol Security](https://arxiv.org/html/2601.17549)
- OWASP Top 10 for Agentic Applications 2026 (ASI01–ASI10)

Tier 2:
- Anthropic Skill Creator Blog, Jan 2026
- Local research: `research/rubric-design/rubric-design-for-llm-evaluators.md`, `research/checklist-calibration/checklist-calibration.md`, `research/verification-methods/verification-methods-per-dimension.md`

## Grade Boundary Calibration (issue #29)

### TL;DR

Rubric grade boundaries `A(90+)/B(80-89)/C(70-79)/D(60-69)/F(<60)` were `[Repo default]` (judgment-set, no calibration evidence). 2026-04-28 calibration run (N=18) produced an empirical distribution of 1A / 8B / 6C / 0D / 3F across rubric-applied grades. The distribution shows no inflation; thresholds are application-consistent at this corpus and require no movement. Annotated as `[Application-checked — N=18, single-rater, calibration_version=2026-04-28]` on `scoring-rubric.md:9`.

### Methodology

`[Repo default — pragmatic given solo maintainer]` Single-rater empirical scoring. 17 of 18 calibration artifacts via single-perspective fallback (multi-perspective Agent dispatch unavailable in calibration session); 1 artifact (review-skill/SKILL.md) reused existing post-2026-04-22 multi-perspective merged report.

`[Out of scope — see successor issue]` Independent ground-truth elicitation was attempted but identified as **methodologically circular** at solo-maintainer scale: the user authored both the rubric and the artifacts being graded, so GT-elicitation reduces to self-grading the rubric. The user explicitly chose closure-via-empirical-distribution-alone instead. This is rubric-application *internal consistency*, not criterion validity.

`[Engineering guidance — RULERS QWK SE > 0.2 at N<30 per llm-evaluator-consistency.md]` No QWK computed — N=18 is below the minimum for QWK SE < 0.2; reporting QWK at this N would mislead.

### Power Analysis

`[Repo default — derived from one-sample-t at N=18, σ_Δ ≈ 0.7]` At N=18 single-rater, this study is powered to detect per-dimension drift ≥ ~0.7 letters at 80% power, α=0.05. Drift smaller than 0.7 letters is below the noise floor of single-rater κ ≈ 0.65. The `[Application-checked]` label reflects this limitation.

### Inverse Problem

`[Repo default — derived from same calc]` An observed cell-disagreement rate of 0% bounds true drift to ±0.4 letters per dimension at 95% CI. This study cannot license claims of finer threshold validity than that.

### Decision Gate

`[Repo default — judgment-set; user-confirmed via AskUserQuestion at decision time]` Gate constants (25% disagreement, 75% directional, ±5pt move) were elicited at decision time, not pre-set numerics. Selected outcome: option 1 — `Application-checked, no move`. Reasoning: empirical distribution does not show inflation; no threshold change is justified by the data.

### Calibration Set (N=18, frozen 2026-04-28)

| ID | Artifact | Anchor | Empirical Overall | Score |
|---|---|---|---|---|
| A1 | skills/review-claude-config/SKILL.md | (proposed A) | B | 86.0 |
| A2 | skills/review-skill/SKILL.md | (proposed A) | B | 84.5 |
| A3 | skills/scaffold-skill/SKILL.md | (proposed A) | C | 77.5 |
| M1 | skills/audit-repo/SKILL.md | mid | B | 83.5 |
| M2 | skills/check-repo-health/SKILL.md | mid | A | 90.0 |
| M3 | skills/audit-context-budget/SKILL.md | mid | C | 77.5 |
| M4 | skills/develop-hooks/SKILL.md | mid | C | 79.0 |
| M5 | skills/scaffold-agent/SKILL.md | mid | B | 81.0 |
| M6 | skills/scaffold-rule/SKILL.md | mid | C | 74.0 |
| M7 | skills/audit-mcp-auth/SKILL.md | mid | B | 81.0 |
| M8 | skills/audit-trust-chain/SKILL.md | mid | C | 75.75 |
| M9 | skills/classify-trace-errors/SKILL.md | mid | B | 81.5 |
| M10 | skills/audit-policy-compliance/SKILL.md | mid | C | 77.35 |
| M11 | skills/scaffold-mcp-server/SKILL.md | mid | B | 80.5 |
| M12 | skills/audit-memory-hygiene/SKILL.md | mid | B | 85.5 |
| F1 | tests/fixtures/eval/case_01_real_issue.SKILL.md | F | F | 53.0 |
| F2 | tests/fixtures/eval/case_05_reliability_agent.md | F | F | 50.0 |
| F3 | tests/fixtures/calibration/clear_f_03_kitchen_sink.SKILL.md | F | F | 50.0 |

Per-artifact reports under `$CLAUDE_PLUGIN_DATA/reports/review-claude-config/2026-04-28T*-review-skill.md` (17 fresh runs) plus `2026-04-22T161232Z-review-skill-runA.md` (A2 reused). Detailed analysis: `research/rubric-design/calibration-runs/2026-04-28-divergence.md`.

### Empirical Distribution

`[Repo default — N=18 corpus tally]`

| Grade | Count | % |
|---|---|---|
| A | 1 | 5.5% |
| B | 8 | 44% |
| C | 6 | 33% |
| D | 0 | 0% |
| F | 3 | 17% |

### Brainstorm-Premise Refutation (issue #29 comment, 2026-04-27)

`[Empirical — N=18 vs 40-report-corpus claim]` The 2026-04-27 brainstorm comment claimed `32A / 7B / 1C across 40 reports = 80% A rate`. The 2026-04-28 calibration corpus (N=18, post-2026-04-22 rubric refresh) shows **5.5% A rate** — refuting the inflation premise by ~14× margin. The 2026-04-22 binary-verifiable items (CLAR-1..4, COMP-W..Z, PE-1/2, SAMP-1/2, SP-2b/4b, IJ-1b, RL-1b/3b/4b/9b, AH-2b, META-1a..4) plus Layer 1.5 boundary caps are demonstrably pushing grades into the B/C band, eliminating the inflation the brainstorm anticipated.

`[Empirical — direct file read]` Brainstorm RC#1 claim that `scoring-rubric.md:12 — "B across all dimensions = A" rule` exists is false: the actual line 12 reads `**Grade derivation:** A=0 FAILs; B=≤25% (no High); C=any High or >25%; D=>50% High; F=>50% total. Cite evidence before grading.` (FAIL aggregation). Brainstorm RC#2 claim that "only A/C/F anchors per dimension" is false: lines 17–69 carry explicit A/B/C/D/F anchors per dimension.

### Limitations (Honest Disclosure)

1. `[Engineering guidance — research/llm-evaluator-consistency/llm-evaluator-consistency.md]` Single-rater empirical scoring at single-rater κ ≈ 0.65. Mixed methodology: 1 of 18 artifacts via multi-perspective merged report, 17 via single-perspective fallback.
2. `[Repo default — solo-maintainer constraint]` No independent ground truth. Solo-maintainer + same-author-as-rubric makes GT-elicitation circular. Lesson saved to `feedback_solo_maintainer_gt_circular.md`.
3. `[Engineering guidance — Round-2 V4 power calc]` N=18 statistical floor: drift below ~0.7 letters indistinguishable from noise.
4. `[Engineering guidance — RULERS arXiv:2407.12366; AdaRubric arXiv:2603.21362]` Criterion validity NOT established. This study measures rubric-application consistency only.
5. `[Repo default — Round-2 V9]` Anchor cohort effective N for divergence: A-anchors 0/3 confirmed (proposed A → empirical B/B/C), F-anchors 3/3 confirmed (engineered convergence). Mid-band (12 items) carries the divergence-detection signal at N=12.

### Successor Tracking

Multi-rater human GT, criterion-validity study (rubric vs production task-success outcomes), and N≥30 corpus expansion are tracked in a successor issue (filed at calibration closure). The `[Application-checked]` annotation supersedes when a future calibration session at higher rigor lands.

### Sources

`[Tier 1]` arXiv:2603.21362 (AdaRubric), arXiv:2407.12366 (RULERS), arXiv:2310.08491 (Prometheus), arXiv:2404.18796 (PoLL k=3 ensemble).
`[Tier 2]` `research/llm-evaluator-consistency/llm-evaluator-consistency.md`, `research/rubric-design/rubric-design-for-llm-evaluators.md`.
