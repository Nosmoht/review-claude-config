---
name: scoring-rubric
description: A-F grading criteria for evaluating Claude Code skills, agents, and rules across type-appropriate dimensions
last_refreshed: 2026-04-08
---

# Scoring Rubric

## Grade Scale
A(90+)=Exemplary, B(80-89)=Good, C(70-79)=Adequate, D(60-69)=Below average, F(<60)=Failing.

**B across all dimensions** = A with one or two minor gaps. **D across all dimensions** = below C but not fully failing.

## Dimensions

### 1. Clarity (15%)
- **A**: Explicit sequential workflow, no ambiguous conditionals, deterministic behavior across runs.
- **B**: All steps sequenced; one conditional broad but not vague.
- **C**: Mostly followable but some steps require interpretation. *if two models would likely produce different workflows from the instructions, it's C or below.*
- **D**: Key dependencies implicit; multiple ambiguous conditionals remain.
- **F**: Vague instructions like "handle appropriately" or "use best judgment" with no criteria.

### 2. Completeness (15%)
- **A**: Edge cases addressed, output format defined, input validation present, failure modes documented; chain-level completeness: handles upstream/downstream dependency failures with progressive fallback (self-correct → fallback → escalate), propagates [INCOMPLETE] or stub-dependency states explicitly rather than silently continuing with partial data.
- **B**: Most errors handled; output format defined; one edge case undocumented.
- **C**: Happy path works but error handling or output format is incomplete. *If a common real-world scenario would cause undefined behavior, it's C or below.*
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
- **C**: Addresses the goal superficially but misses domain-critical aspects. *if a domain expert would identify obvious missing steps or checks, it's C or below.*
- **D**: Goal met but misses multiple domain-critical aspects practitioners expect.
- **F**: Goal stated in description but body doesn't support achieving it.

### 6. Safety (10%; 15% with Write/Bash/Edit)
- **A**: Least-privilege tool scoping per archetype (`tool-grant-decision-tree.md`), explicit guardrails for destructive actions, stop conditions, confirmation gates; failure path defined for every external dependency; stop condition prevents infinite recursion.
- **B**: Least-privilege with one exception; gates present; one failure path implicit.
- **C**: Tools are broader than needed or guardrails are implicit; any unmitigated Tier A high-risk combination (see `tool-grant-decision-tree.md`) caps Safety at C. *if the item could modify/delete user data without explicit confirmation, it's C or below.*
- **D**: Multiple tools too broad; no gates; some stop conditions missing.
- **F**: Unrestricted tools with no guardrails. No stop conditions.

> **Agentic overlay** (applies when item has multi-step workflows, subagent delegation, loop/retry logic, or Write/Bash/Edit tools): R1-R10 reliability checks apply per `autonomous-agent-reliability.md` §Quality Rubric Checks. High-severity checks (R1: termination conditions, R4: escalation/HITL, R9: safety/PII scope) are B/C discriminators — missing any High check caps Safety at C. Grade mapping: **A** = all 10 addressed; **B** = all High checks addressed, ≤2 Medium implicit; **C-F** = inherit base grades, each missing High check shifts one grade down.

> **Execution diagnostics:** RD-6 (tool availability probe) contributes to Safety; RD-4 (error handling for tool unavailability and unexpected output) contributes to Completeness; RD-5 (explicit step dependencies) contributes to Clarity.

### 7. Metadata (10%; 5% if Safety is 15%)
- **A**: Complete frontmatter, description matches body, tool list matches usage, argument-hint present, trigger conditions explicit.
- **B**: Complete frontmatter; one minor tool list mismatch.
- **C**: Required fields present but description is vague or tool list doesn't match usage. *If the description would cause incorrect skill/agent selection, it's C or below.*
- **D**: Required fields present; description vague AND multiple tool list mismatches.
- **F**: Missing required fields or description is misleading.

For agent-specific criteria, see `agent-evaluation-guide.md`. R1-R10 definitions: `autonomous-agent-reliability.md` §Quality Rubric Checks.

> **Activation diagnostics:** RD-1 (trigger ambiguity), RD-2 (negative constraints), RD-3 (trigger overlap with siblings) contribute activation-failure evidence to Metadata grading. Any RD-1/2/3 FAIL indicates activation reliability risk.

## Reviewer Output Expectations

Every High or Medium recommendation must cite concrete evidence, explain impact, include `Current:` and `Recommended:` blocks when a rewrite is feasible, and add a `Validation:` line. Omit or mark Low cosmetic issues that don't affect trigger, safety, or completeness.

## Conditional Weighting
Tools with Write/Bash/Edit: Safety→15%, Meta→5%; otherwise Safety→10%, Meta→10%.

## Rule-Specific Scoring
Rules use only 3 dimensions (renormalized): Clarity 30%, Completeness 30%, Goal Alignment 40%. Skip: PE, CE, Safety, Metadata (rules have no tools, no frontmatter, and are directives not prompts).

**Hard rule:** Every rule review MUST produce grades for all 3 dimensions. A rule report with any dimension set to `null` is INVALID — re-evaluate the missing dimension before finalizing the certificate.
