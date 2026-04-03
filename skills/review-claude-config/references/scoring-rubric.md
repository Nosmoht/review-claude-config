---
name: scoring-rubric
description: A-F grading criteria for evaluating Claude Code skills, agents, and rules across type-appropriate dimensions
---

# Scoring Rubric

## Grade Scale
A(90+)=Exemplary, B(80-89)=Good, C(70-79)=Adequate, D(60-69)=Below average, F(<60)=Failing.

**B across all dimensions** = A with one or two minor gaps. Prompt Engineering B: 3+ techniques used effectively.

## Dimensions

### 1. Clarity (15%) — Can a model follow this unambiguously?
- **A**: Explicit sequential workflow, no ambiguous conditionals, deterministic behavior across runs.
- **C**: Mostly followable but some steps require interpretation. *if two models would likely produce different workflows from the instructions, it's C or below.*
- **F**: Vague instructions like "handle appropriately" or "use best judgment" with no criteria.

### 2. Completeness (15%) — Are all cases handled?
- **A**: Edge cases addressed, output format defined, input validation present, failure modes documented.
- **C**: Happy path works but error handling or output format is incomplete. *If a common real-world scenario would cause undefined behavior, it's C or below.*
- **F**: Only describes the goal, not how to achieve it. No output specification.

### 3. Prompt Engineering (15%) — Does it use proven techniques?
- **A**: Uses structured output templates, role priming, few-shot examples where appropriate, explicit constraints, verification criteria, and evidence-first wording for review tasks.
- **C**: Uses 1-2 techniques or uses them ineffectively. *if the item relies entirely on implicit model behavior without any explicit technique, it's C or below.*
- **F**: Raw instructions with no prompting techniques. No output format, no examples, no constraints.

### 4. Context Engineering (15%) — Is context managed efficiently?
- **A**: Minimal tool set, JIT retrieval, reference files for stable knowledge, concise output format, subagent isolation where appropriate, and activation precision that avoids false triggering.
- **C**: Functional but loads unnecessary context or has bloated tool set. *If a human engineer can't immediately say which tool to use for a given situation, it's C or below.*
- **F**: Kitchen-sink tool list, all information pre-loaded, no concern for context budget.

### 5. Goal Alignment (20%) — Will it actually achieve its stated goal?
- **A**: Has the right domain knowledge, tools, and structure. Domain best practices are reflected in workflow and checks, and a reviewer would not need to guess why a finding exists.
- **C**: Addresses the goal superficially but misses domain-critical aspects. *if a domain expert would identify obvious missing steps or checks, it's C or below.*
- **F**: Goal stated in description but body doesn't support achieving it.

### 6. Safety (10%, or 15% if item has Write/Bash/Edit tools)
- **A**: Least-privilege tool scoping, explicit guardrails for destructive actions, stop conditions, confirmation gates.
- **C**: Tools are broader than needed or guardrails are implicit. *if the item could modify/delete user data without explicit confirmation, it's C or below.*
- **F**: Unrestricted tools with no guardrails. No stop conditions.

### 7. Metadata (10%, or 5% if Safety is 15%)
- **A**: Complete frontmatter, description accurately matches body, tool list matches actual usage, argument-hint present if applicable, and the description states what the item does plus when it should trigger.
- **C**: Required fields present but description is vague or tool list doesn't match usage. *If the description would cause incorrect skill/agent selection, it's C or below.*
- **F**: Missing required fields or description is misleading.

For agent-specific criteria (example blocks, activation precision, model selection), see `agent-evaluation-guide.md`.

## Reviewer Output Expectations

Every High or Medium recommendation must cite concrete evidence, explain impact, include `Current:` and `Recommended:` blocks when a rewrite is feasible, and add a `Validation:` line. Omit or mark Low cosmetic issues that don't affect trigger, safety, or completeness.

## Conditional Weighting
Tools with Write/Bash/Edit: Safety→15%, Meta→5%; otherwise Safety→10%, Meta→10%.

## Rule-Specific Scoring
Rules use only 3 dimensions (renormalized): Clarity 30%, Completeness 30%, Goal Alignment 40%. Skip: PE, CE, Safety, Metadata (rules have no tools, no frontmatter, and are directives not prompts).
