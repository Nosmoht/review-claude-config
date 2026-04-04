---
generated_by: review-skill
schema_version: 1
date: 2026-04-04
target: /Users/ntbc/workspace/review-claude-config/skills/scaffold-agent/SKILL.md
baseline_version: 2026-04-03
items_reviewed: 1
summary:
  - name: scaffold-agent
    type: Skill
    path: skills/scaffold-agent/SKILL.md
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

# Review: skills/scaffold-agent/SKILL.md

## Goal
Generate valid Claude Code agent `.md` files with correct frontmatter, example blocks, and numbered workflow body, then register them in repository documentation — guided by interactive requirement gathering and user confirmation before file creation.

## Certificate

| Dimension | Grade | Weight | Justification |
|-----------|-------|--------|---------------|
| Clarity | A | 15% | Seven numbered steps have explicit sequential dependencies, deterministic conditionals (yes/edit/cancel), and stop conditions anchored to observable events. |
| Completeness | B | 15% | Happy path and most edge cases covered; write-failure recovery documented; missing: stop condition if references/agent-template.md is absent, and no retry ceiling on invalid-name loop. |
| Prompt Engineering | B | 15% | Role priming, few-shot output example, constraint specification, and stepwise decision flow all present; verification criteria absent (no self-check that generated frontmatter meets documented field limits). |
| Context Engineering | A | 15% | JIT template load in Step 2, optional research file loaded only if found, disable-model-invocation: true prevents accidental activation, allowed-tools minimal (Read/Write/Edit/Glob), reference content separated. |
| Goal Alignment | A | 20% | Workflow aligns with official Anthropic skill-authoring guidance: least-privilege tools, interactive requirement gathering, preview gate, additive doc edits, model selection table, kebab-case naming enforced. |
| Safety | A | 15% | Confirmation gate before write (Step 4 yes/edit/cancel), overwrite guard (Hard Rules), stop conditions on invalid name / cancel / write failure, additive-only doc edits, least-privilege tool set. |
| Metadata | B | 5% | All required frontmatter fields present; argument-hint correct; description triggers well but does not state when not to use (e.g., adding to external projects beyond this repo). |
| **Overall** | **A** | **100%** | **Weighted: 91.5 → A** |

Safety=15%, Metadata=5% (Write/Edit in allowed-tools).

## Strengths

- Confirmation gate (yes/edit/cancel preview in Step 4) before any file write is textbook safety practice for scaffolding skills with Write access.
- JIT reference loading: template read in Step 2, research file conditionally loaded with a Glob fallback — keeps context budget lean on fast runs.
- `disable-model-invocation: true` prevents accidental agent-invocation chains, appropriate for a file-writing skill.
- Hard Rules section enforces all critical constraints redundantly (overwrite guard, valid frontmatter-only fields, additive-only doc edits), making them resilient even if mid-workflow context narrows.
- The few-shot output example for a `pr-reviewer` agent is concrete and covers all required sections, giving the model a reliable structural target.

## Recommendations

### 1. Add missing-template stop condition (Impact: Medium, Category: Workflow)

**Evidence:** Step 2 reads `references/agent-template.md` but provides no instruction for what to do if the file is not found. The optional research file has a Glob-with-fallback pattern, but the required template does not.

**Why it matters:** If the template file is missing (corrupted install, partial plugin deployment), the skill silently continues with no structural reference, producing malformed output. Per the Completeness rubric, a common real-world scenario causing undefined behavior scores C or below on that dimension.

**Validation:** Re-review — Completeness dimension should rise to A when the missing-file stop is explicit.

**Current:**
```
Read `references/agent-template.md` for the canonical agent .md structure and model selection guidance.
```

**Recommended:**
```
Read `references/agent-template.md` for the canonical agent .md structure and model selection guidance.

If the file is not found, report: "Required template not found at `references/agent-template.md`. Ensure scaffold-agent is correctly installed." and stop.
```

---

### 2. Add verification step for generated frontmatter validity (Impact: Medium, Category: Prompt)

**Evidence:** Step 4 generates frontmatter and shows it for user review, but there is no explicit check that `description` ≤ 1024 chars, `name` ≤ 64 chars, or that no XML tags are present. These are documented Anthropic frontmatter constraints.

**Why it matters:** The engineering baseline specifies "Verification Criteria — tell the agent how to confirm correctness using checks or expected outcomes." A user-approved preview does not substitute for the agent self-checking the generated content against known field constraints before writing.

**Validation:** Re-review — Prompt Engineering dimension should rise to A when verification criteria cover the field limits.

**Current:**
```
Present the full generated content to the user for review. Ask: "Does this look correct? (yes/edit/cancel)"
```

**Recommended:**
```
Before presenting for review, verify:
- `name` is kebab-case, ≤ 64 chars, does not contain "anthropic" or "claude".
- `description` is ≤ 1024 chars and contains no XML tags.
- No frontmatter fields beyond: `name`, `description`, `model`, `color`, `tools`, `allowed-tools`.

If any check fails, fix the generated content and re-verify before presenting.

Present the full generated content to the user for review. Ask: "Does this look correct? (yes/edit/cancel)"
```

---

### 3. Add retry ceiling for invalid-name loop (Impact: Low, Category: Safety)

**Evidence:** Step 1 says "report the specific issue and ask for a corrected name. Stop and wait — do not continue until a valid name is provided." There is no ceiling on how many times the user can re-submit an invalid name.

**Why it matters:** The engineering baseline lists Retry Ceilings as a repo default: "keep the retry budget small and explicit so failures escalate instead of looping invisibly."

**Validation:** Safety dimension remains A; this is a low-priority hardening improvement.

**Current:**
```
If validation fails, report the specific issue and ask for a corrected name. Stop and wait — do not continue until a valid name is provided.
```

**Recommended:**
```
If validation fails, report the specific issue and ask for a corrected name. Stop and wait.
After three failed attempts, report: "Name validation failed three times. Stopping to avoid loop. Invoke /scaffold-agent again with a valid agent name." and stop.
```
