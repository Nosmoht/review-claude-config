---
name: scoring-rubric
description: A-F grading criteria for evaluating Claude Code skills, agents, and rules across type-appropriate dimensions
---

# Scoring Rubric

## Grade Scale
A(90+)=Exemplary, B(80-89)=Good, C(70-79)=Adequate, D(60-69)=Below average, F(<60)=Failing.

## Dimensions

### 1. Clarity (15%) — Can a model follow this unambiguously?
- **A**: Explicit sequential workflow, no ambiguous conditionals, deterministic behavior across runs.
- **B**: Clear workflow with minor ambiguities that rarely affect execution.
- **C**: Mostly followable but some steps require interpretation. *if two models would likely produce different workflows from the instructions, it's C or below.*
- **F**: Vague instructions like "handle appropriately" or "use best judgment" with no criteria.

### 2. Completeness (15%) — Are all cases handled?
- **A**: Edge cases addressed, output format defined, input validation present, failure modes documented.
- **B**: Core cases covered, output format defined, minor edge cases missing.
- **C**: Happy path works but error handling or output format is incomplete. *If a common real-world scenario would cause undefined behavior, it's C or below.* For Agents: evaluate `<example>` blocks for trigger pattern coverage. *If no examples and description is ambiguous, it's C or below.*
- **F**: Only describes the goal, not how to achieve it. No output specification.

### 3. Prompt Engineering (15%) — Does it use proven techniques?
- **A**: Uses structured output templates, role priming, few-shot examples where appropriate, explicit constraints, verification criteria, and evidence-first wording for review tasks.
- **B**: Uses 3+ techniques effectively.
- **C**: Uses 1-2 techniques or uses them ineffectively. *if the item relies entirely on implicit model behavior without any explicit technique, it's C or below.*
- **F**: Raw instructions with no prompting techniques. No output format, no examples, no constraints.

### 4. Context Engineering (15%) — Is context managed efficiently?
- **A**: Minimal tool set, JIT retrieval, reference files for stable knowledge, concise output format, subagent isolation where appropriate, and activation precision that avoids false triggering.
- **B**: Good tool scoping, reasonable context awareness, minor bloat.
- **C**: Functional but loads unnecessary context or has bloated tool set. *If a human engineer can't immediately say which tool to use for a given situation, it's C or below.* For Agents: evaluate description and example blocks for activation precision, not progressive disclosure. *If description is generic enough to match unrelated user requests, it's C or below.*
- **F**: Kitchen-sink tool list, all information pre-loaded, no concern for context budget.

### 5. Goal Alignment (20%) — Will it actually achieve its stated goal?
- **A**: Has the right domain knowledge, tools, and structure. Domain best practices are reflected in workflow and checks, and a reviewer would not need to guess why a finding exists.
- **B**: Mostly aligned with domain needs, minor gaps in coverage.
- **C**: Addresses the goal superficially but misses domain-critical aspects. *if a domain expert would identify obvious missing steps or checks, it's C or below.*
- **F**: Goal stated in description but body doesn't support achieving it.

### 6. Safety (10%, or 15% if item has Write/Bash/Edit tools)
- **A**: Least-privilege tool scoping, explicit guardrails for destructive actions, stop conditions, confirmation gates.
- **B**: Appropriate tool scoping, some guardrails present.
- **C**: Tools are broader than needed or guardrails are implicit. *if the item could modify/delete user data without explicit confirmation, it's C or below.*
- **F**: Unrestricted tools with no guardrails. No stop conditions.

### 7. Metadata (10%, or 5% if Safety is 15%)
- **A**: Complete frontmatter, description accurately matches body, tool list matches actual usage, argument-hint present if applicable, and the description states what the item does plus when it should trigger.
- **B**: Complete frontmatter, description mostly accurate.
- **C**: Required fields present but description is vague or tool list doesn't match usage. *If the description would cause incorrect skill/agent selection, it's C or below.* For Agents: if `model` is specified, verify appropriateness for task complexity (haiku for simple checks, sonnet for analysis, opus for complex reasoning). *If `model` is specified but clearly mismatched to task complexity, it's C or below.*
- **F**: Missing required fields or description is misleading.

## Reviewer Output Expectations

Every High or Medium recommendation should:
- cite concrete evidence from the target file or external source
- explain why the issue matters in one short paragraph
- include `Current:` and `Recommended:` blocks when an exact rewrite is feasible
- include a `Validation:` line describing how to confirm the fix on re-review
- keep isolated cosmetic wording issues Low impact or omit them entirely unless they create a concrete trigger, safety, or completeness problem

## Conditional Weighting
Tools with Write/Bash/Edit: Safety→15%, Meta→5%; otherwise Safety→10%, Meta→10%.

## Rule-Specific Scoring
Rules use only 3 dimensions (renormalized): Clarity 30%, Completeness 30%, Goal Alignment 40%. Skip: PE, CE, Safety, Metadata (rules have no tools, no frontmatter, and are directives not prompts).
