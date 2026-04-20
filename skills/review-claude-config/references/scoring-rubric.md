---
name: scoring-rubric
description: A-F grading criteria for evaluating Claude Code skills, agents, and rules across type-appropriate dimensions
last_refreshed: 2026-04-20
---

# Scoring Rubric

## Grade Scale
A(90+)=Exemplary, B(80-89)=Good, C(70-79)=Adequate, D(60-69)=Below average, F(<60)=Failing.

**Grade derivation:** A=0 FAILs; B=≤25% (no High); C=any High or >25%; D=>50% High; F=>50% total. Cite evidence before grading.

## Dimensions

### 1. Clarity (15%)
- **A**: Explicit sequential workflow, no ambiguous conditionals, deterministic behavior across runs.
- **B**: All steps sequenced; one conditional broad but not vague.
- **C**: Mostly followable but some steps require interpretation. *Test: any conditional uses a bare vague predicate ("if needed", "as appropriate") without a concrete trigger, OR any step parameter uses a fuzzy quantifier ("slightly", "a bit", "some", "roughly"), OR any instruction contains an unresolved pronoun referring to prior tool output → C or below.*
- **D**: Key dependencies implicit; multiple ambiguous conditionals remain.
- **F**: Vague instructions like "handle appropriately" or "use best judgment" with no criteria.

### 2. Completeness (15%)
- **A**: Edge cases addressed, output format defined, input validation present, failure modes documented; chain-level completeness: handles upstream/downstream dependency failures with progressive fallback (self-correct → fallback → escalate), propagates [INCOMPLETE] or stub-dependency states explicitly rather than silently continuing with partial data.
- **B**: Most errors handled; output format defined; one edge case undocumented.
- **C**: Happy path works but error handling or output format is incomplete. *Test: any declared input can reach a path with no defined output or error handling → C or below.*
- **D**: Multiple errors undefined; output format absent or vague.
- **F**: Only describes the goal, not how to achieve it. No output specification.

### 3. Prompt Engineering (15%)
- **A**: Uses structured output, role priming, few-shot examples, explicit constraints, verification criteria, and evidence-first wording.
- **B**: 3+ techniques effective; output and constraints explicit; minor gaps.
- **C**: Uses 1-2 techniques or uses them ineffectively. *if the item relies entirely on implicit model behavior without any explicit technique, it's C or below.*
- **D**: 1 technique inconsistent; output partially defined; mostly implicit.
- **F**: Raw instructions with no prompting techniques. No output format, no examples, no constraints.

### 4. Context Engineering (15%)
- **A**: Minimal tool set, JIT retrieval, reference files for stable knowledge, subagent isolation where appropriate, activation precision; instruction density within reliable-adherence range (≤10 distinct constraints, ≤2,000 words, ≤30% conditional constraints) OR high density mitigated via structured sections, priority ordering, or few-shot examples.
- **B**: Appropriate tools with one exception; progressive disclosure mostly applied; OR instruction density exceeds range (>10 constraints or >2,000 words) but structural mitigations compensate.
- **C**: Functional but loads unnecessary context or has bloated tool set; OR instruction density exceeds reliable-adherence range without mitigations (>10 distinct constraints or >2,000 words; conditional constraints >30% of body). *If a human engineer can't immediately say which tool to use for a given situation, it's C or below. AgentIF (arXiv:2505.16944): ISR drops to <30% at avg 11.9 constraints; condition constraints fail at 19.1% vs 66.8% for formatting constraints.*
- **D**: Multiple tools too broad; stable content inlined; noticeable bloat; OR unmitigated density >6,000 words (near-zero ISR across all models).
- **F**: Kitchen-sink tool list, all information pre-loaded, no concern for context budget.

> **Model taxonomy note** (IFScale, arXiv:2507.11538): Thresholds above are calibrated for **linear-decay models** (Claude Sonnet class — steady accuracy loss from early density increases). **Reasoning models** (o3, Gemini-2.5-Pro) follow threshold decay and sustain near-perfect adherence through ~150+ instructions — apply a higher B/C boundary when explicitly reviewing skills targeting those models.

### 5. Goal Alignment (20%)
- **A**: Has right domain knowledge, tools, and structure; best practices reflected in workflow; findings self-evident to reviewers.
- **B**: Domain-appropriate structure; one aspect superficially covered.
- **C**: Addresses the goal superficially but misses domain-critical aspects. *Test: workflow omits a step flagged FAIL by the evaluation checklist → C or below.*
- **D**: Goal met but misses multiple domain-critical aspects practitioners expect.
- **F**: Goal stated in description but body doesn't support achieving it.

### 6. Safety (10%; 15% with Write/Bash/Edit)
- **A**: Least-privilege tool scoping per archetype (`tool-grant-decision-tree.md`), explicit guardrails for destructive actions, stop conditions, confirmation gates; failure path defined for every external dependency; stop condition prevents infinite recursion.
- **B**: Least-privilege with one exception; gates present; one failure path implicit.
- **C**: Tools broader than needed or guardrails implicit; unmitigated Tier A combination caps Safety at C. *Test: item modifies/deletes user data without explicit confirmation → C or below.*
- **D**: Multiple tools too broad; no gates; some stop conditions missing.
- **F**: Unrestricted tools with no guardrails. No stop conditions.

> **Agentic overlay** (applies when item has multi-step workflows, subagent delegation, loop/retry logic, or Write/Bash/Edit tools): R1-R10 reliability checks apply per `autonomous-agent-reliability.md` §Quality Rubric Checks. High-severity checks (R1: termination conditions, R4: escalation/HITL, R9: safety/PII scope) are B/C discriminators — missing any High check caps Safety at C. Grade mapping: **A** = all 10 addressed; **B** = all High checks addressed, ≤2 Medium implicit; **C-F** = inherit base grades, each missing High check shifts one grade down.

> **Execution diagnostics:** RD-6 (tool availability probe) contributes to Safety; RD-4 (error handling for tool unavailability and unexpected output) contributes to Completeness; RD-5 (explicit step dependencies) contributes to Clarity.

### 7. Metadata (10%; 5% if Safety is 15%)
- **A**: Complete frontmatter, description matches body, tool list matches usage, argument-hint present, trigger conditions explicit.
- **B**: Complete frontmatter; one minor tool list mismatch.
- **C**: Required fields present but description is vague or tool list doesn't match usage. *Test: description lacks a primary verb+object or contains no discriminating keyword → C or below.*
- **D**: Required fields present; description vague AND multiple tool list mismatches.
- **F**: Missing required fields or description is misleading.

For agent-specific criteria, see `agent-evaluation-guide.md`. R1-R10 definitions: `autonomous-agent-reliability.md` §Quality Rubric Checks.

> **Activation diagnostics:** RD-1 (trigger ambiguity), RD-2 (negative constraints), RD-3 (trigger overlap with siblings) contribute activation-failure evidence to Metadata grading. Any RD-1/2/3 FAIL indicates activation reliability risk.

## Reviewer Output Expectations

High/Medium recommendations must cite evidence, explain impact, include `Current:`/`Recommended:` blocks, and a `Validation:` line. Omit Low cosmetic issues.

## Conditional Weighting
Tools with Write/Bash/Edit: Safety→15%, Meta→5%; otherwise Safety→10%, Meta→10%.

## Rule-Specific Scoring
Rules use only 3 dimensions (renormalized): Clarity 30%, Completeness 30%, Goal Alignment 40%. Skip: PE, CE, Safety, Metadata (rules have no tools, no frontmatter, and are directives not prompts).

**Hard rule:** Every rule review MUST produce grades for all 3 dimensions. A rule report with any dimension set to `null` is INVALID — re-evaluate the missing dimension before finalizing the certificate.

## MCP/Settings Scoring
4 dims: Compl 25%, GA 25%, Safety 30%, Meta 20%. Skip Clarity/PE/CE.

## Plugin Scoring
4 dims: Compl 25%, GA 25%, Safety 30%, Meta 20%. See `skills/review-plugin/references/plugin-evaluation-guide.md`.

## Binary-Verifiable Rubric Items (issues #4/#5/#6/#10/#62/#66)

Each item below is binary (PASS/FAIL via regex/glob/count/LLM-binary)
with documented BOUNDARY PASS / BOUNDARY FAIL exemplars. See
`research/rubric-design/rubric-calibration-evidence.md` for evidence
sources (Tier-1 cited per item).

### Trigger-Consistency (Metadata B/C discriminator) — issue #4

- **META-1a Trigger-Match-Primary**: `description` contains the body's primary trigger keyword. *Verification:* token-set overlap. *PASS:* "Use when reviewing MCP server configs" + body triggers on `.mcp.json`. *FAIL:* body triggers on `.mcp.json` but description says "Use for configurations".
- **META-1b Trigger-Match-Generalisation**: OR-joined with META-1a — description uses "when", "for", or a domain term that covers a broader trigger.
- **META-2 Anti-Pattern Example**: description contains `/do ?not use|not for|skip (when|if)/i`. *PASS:* "Do NOT use for agents or rules — use /review-agent instead." *FAIL:* "Use this skill when you need to review a skill."
- **META-3a Concrete Trigger**: no description uses `/as needed|if appropriate|when useful/i`. *PASS:* "when file contains hooks.json". *FAIL:* "use as appropriate".
- **META-3b Sibling-Distinguishability**: no sibling SKILL.md in the same plugin shares ≥2 trigger keywords (token-set overlap).
- **META-4 Third-Person Description** — issue #62: frontmatter `description` field uses third person throughout. *Verification:* regex exclusion on the rendered description block — no first-person (`\bI\s`, `\bmy\s`, `\bme\s`, case-sensitive on `I`) and no second-person imperative (`\byou can\s`, `\byour\s`, case-insensitive). *PASS:* "Evaluates MCP server configs and produces a quality certificate." *FAIL:* "I help you review your MCP configs." Source: Anthropic Skills best-practices (Warning block) — "Always write in third person. The description is injected into the system prompt, and inconsistent point-of-view can cause discovery problems."

Grade boundary: META-1 ✗ → D/F (dispatch failure); META-2 ✗ → C; META-4 ✗ → C (third-person violation = discovery risk); all ✓ → B; all ✓ + no sibling overlap → A.

### Ambiguity Markers (Clarity B/C discriminator) — issue #66

- **CLAR-1 Fuzzy-Quantifier-Free**: step parameters contain no fuzzy quantifier. *Regex:* `/\b(slightly|a bit|roughly|somewhat|some)\b/i` (skip `some` inside placeholder paths). *PASS:* "fetch 10 entries". *FAIL:* "fetch roughly 10 entries".
- **CLAR-2 Resolved-Pronoun**: pronouns referring to prior tool outputs (`it`/`them`/`that`/`this`/`those`) have an explicit antecedent in the same or immediately-preceding step. *Verification:* LLM-binary. *PASS:* "parse the grep output; store the matches". *FAIL:* "parse the output; then process them".

Grade boundary: CLAR-1 ✗ OR CLAR-2 ✗ → Clarity capped at C. Source: arXiv:2507.11525 (ambiguity taxonomy, F1=0.83 Gemma 3 12B); arXiv:2512.14754 (IFEval++ reliable@k, 61.8 % accuracy drop).

### Observation-Masking Parity (CE Grade-A) — issue #5

- **CE-X Compaction-Strategy Declaration**: if the workflow keeps conversation history ≥10 turns AND uses LLM-based summarisation, the skill body contains ≥1 sentence justifying why masking is insufficient. See engineering-baseline.md §"Observation Masking" decision table for the (a)/(b)/(c) cases.

### Verification Criteria (Completeness Grade-A) — issue #6

- **COMP-X Success Criteria**: explicit success condition defined, not just output format. *Verification:* count of "complete when|success when|done when" patterns in body.
- **COMP-Y Verification Method**: programmatic check or explicit binary LLM item (not holistic "looks good"). *Exclusion regex:* `/looks good|seems correct|appears valid/i`.
- **COMP-Z Evidence Trail**: verification-decision evidence recorded. *Regex:* `/evidence|citation|quote|verified against/i` in output spec.

### Task-Type Resolution — issue #10

Before dimension scoring, run the heuristic-first resolution algorithm in
`research/rubric-design/task-type-rubric-variants.md` §"Resolution
Algorithm". The chosen task type (orchestrator | code-review |
research-synthesis | scaffold | tutoring | general-purpose) selects the
override table that adjusts dimension weights. Override choice + LLM
justification (when applied) are logged in the report certificate.

### Sampling-Param Migration (PE/Metadata) — Opus 4.7

- **SAMP-1 (PE-body)**: skill/agent body free of hardcoded `temperature`/`top_p`/`top_k` (regex `/\b(temperature|top_p|top_k)\s*[:=]/i`). FAIL caps PE at C.
- **SAMP-2 (Metadata frontmatter)**: frontmatter override block free of removed sampling params. FAIL is hard F (runtime 400-error on Opus 4.7).
