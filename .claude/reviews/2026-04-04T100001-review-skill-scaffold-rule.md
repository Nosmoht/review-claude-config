---
generated_by: review-skill
schema_version: 1
date: 2026-04-04
target: /Users/ntbc/workspace/review-claude-config/skills/scaffold-rule/SKILL.md
baseline_version: 2026-04-03
items_reviewed: 1
summary:
  - name: scaffold-rule
    type: Skill
    path: skills/scaffold-rule/SKILL.md
    overall: A
    score: 91.5
    clarity: A
    completeness: B
    prompt_engineering: B
    context_engineering: A
    goal_alignment: A
    safety: A
    metadata: B
---

# Review: skills/scaffold-rule/SKILL.md

## Goal
Generate correctly structured Claude Code rule files (plain Markdown, no frontmatter) by interactively gathering requirements and writing to `.claude/rules/<rule-name>.md` with a confirmation gate before any file creation.

## Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Seven numbered steps with clear sequential dependencies; confirmation gate branches (yes/edit/cancel) are deterministic; stop conditions tied to observable events. |
| Completeness | B | 15% | Happy path, overwrite guard, and write-failure reporting are documented; missing: explicit stop if references/rule-template.md is absent, and no retry ceiling on the invalid-name loop. |
| Prompt Engineering | B | 15% | Role priming, constraint specification, inline output template, and stepwise decision flow all present; verification criteria absent (no self-check that generated output contains no frontmatter before presenting). |
| Context Engineering | A | 15% | Template read JIT in Step 2, optional research file Glob-with-fallback, disable-model-invocation: true, minimal allowed-tools (Read/Write/Edit/Glob), reference content separated. |
| Goal Alignment | A | 20% | Scaffold matches official guidance: plain-Markdown rules, no frontmatter, strong enforcement verbs from template, consolidation check for constraint load, additive-only doc edits. |
| Safety | A | 15% | Confirmation gate before write (yes/edit/cancel in Step 4), overwrite guard in Hard Rules, stop conditions on invalid name / cancel / write failure, additive-only doc edits enforced. |
| Metadata | B | 5% | All frontmatter fields present and accurate; argument-hint correct; description does not state when not to use (e.g., should not be used to scaffold skills or agents). |
| **Overall** | **A** | **100%** | **Weighted: 91.5 → A** |

Safety=15%, Metadata=5% (Write/Edit in allowed-tools).

## Strengths

- The consolidation-check requirement in Step 3 ("if 5 or more rules cover similar themes, suggest consolidating") directly addresses the constraint-load problem documented in the rule template — this is domain-aware design.
- `disable-model-invocation: true` prevents accidental chain-invocation; appropriate for a file-writing skill with side effects.
- The inline output template in Step 4 is complete (title, directive, Scope, Edge Cases) and matches the canonical rule structure from the reference, giving the model a precise structural target.
- Hard Rules redundantly enforce the most critical constraints (no overwrite, no frontmatter, preview-before-write, additive docs) — making them resilient when mid-workflow context degrades.
- Step 6 correctly uses `Edit` for targeted additive registration and explicitly handles the case where a heading does not exist (skip and note), avoiding hallucinated section creation.

## Recommendations

### 1. Add missing-template stop condition (Impact: Medium, Category: Workflow)

**Evidence:** Step 2 reads `references/rule-template.md` with no fallback or stop instruction if the file is not found. The optional research file has explicit Glob-with-fallback handling, but the required template does not.

**Why it matters:** A partial or corrupted install will cause the skill to proceed without its structural reference, silently generating output from model defaults rather than the canonical template. Per the Completeness rubric, a common real-world scenario that causes undefined behavior scores C or below on that dimension.

**Validation:** Re-review — Completeness dimension should rise to A when the missing-file stop is explicit.

**Current:**
```
Read `references/rule-template.md` for the canonical rule structure.
```

**Recommended:**
```
Read `references/rule-template.md` for the canonical rule structure.

If the file is not found, report: "Required template not found at `references/rule-template.md`. Ensure scaffold-rule is correctly installed." and stop.
```

---

### 2. Add pre-presentation verification for no-frontmatter constraint (Impact: Medium, Category: Prompt)

**Evidence:** Step 4 generates the rule and presents it for user review, but there is no explicit self-check that the generated output contains no YAML frontmatter block. The Hard Rules state "Rules have no frontmatter" but there is no verification step before presenting.

**Why it matters:** The engineering baseline specifies "Verification Criteria — tell the agent how to confirm correctness using checks or expected outcomes." The rule format constraint (no frontmatter) is critical and easy to violate if the model generalises from skill/agent scaffolding patterns. A pre-presentation check makes this machine-verifiable rather than relying on user review.

**Validation:** Re-review — Prompt Engineering dimension should rise to A when a self-verification pass is specified before the preview.

**Current:**
```
Present the full generated content to the user. Ask: "Does this look correct? (yes/edit/cancel)"
```

**Recommended:**
```
Before presenting, verify:
- The generated content has NO YAML frontmatter block (no `---` delimiters at the top).
- The content starts with `# <Rule Name>` as the first line.
- The directive uses strong enforcement verbs (always / never / before X do Y / only when / stop if) — not weak phrasing like "try to" or "prefer".

If any check fails, fix the generated content and re-verify before presenting.

Present the full generated content to the user. Ask: "Does this look correct? (yes/edit/cancel)"
```

---

### 3. Narrow the description trigger (Impact: Low, Category: Metadata)

**Evidence:** The description reads: `"Use when adding a new always-active constraint to a project."` This does not exclude cases where the user might intend to scaffold a skill or agent instead, and does not mention `.claude/rules/` as the distinguishing output.

**Why it matters:** Activation precision — the description is the primary trigger for skill selection. Making the output location explicit and adding a negative trigger prevents mis-selection against scaffold-skill or CLAUDE.md edit requests.

**Validation:** Re-review — Metadata dimension should rise to A.

**Current:**
```
description: >
  Create a new Claude Code rule file at .claude/rules/<rule-name>.md with the
  canonical plain-Markdown structure: title, directive statement, scope, and
  edge cases. Use when adding a new always-active constraint to a project.
```

**Recommended:**
```
description: >
  Create a new Claude Code rule file at .claude/rules/<rule-name>.md with the
  canonical plain-Markdown structure: title, directive statement, scope, and
  edge cases. Use when adding a new always-active constraint that belongs in
  .claude/rules/. Do not use for CLAUDE.md edits, skills, or agents.
```
