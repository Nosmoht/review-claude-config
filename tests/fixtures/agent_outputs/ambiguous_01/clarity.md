### Perspective
clarity

### Certificate
| Dimension | Grade | Justification |
|-----------|-------|---------------|
| Clarity | C | WS-2 FAIL: Step 3 conditional "if relevant" lacks a concrete trigger; WS-1 FAIL: Step 4 references "the file" without naming which file or which step produced it. |
| Completeness | B | Most error paths covered. |
| Prompt Engineering | B | Output contract present. |
| Context Engineering | B | references/ loaded correctly. |
| Goal Alignment | B | Intent stated. |
| Safety | B | Read-only tools. |
| Metadata | B | Frontmatter complete. |
| Overall | C | Two High Clarity findings cap Clarity at C; no other grade-boundary violations. |

### Findings

#### Finding (severity: High, dimension: Clarity, checklist_item: WS-1, primary_focus: true, owner_conflict: false, hint_owner: null)
Evidence: "Step 4: Read the file and extract the metadata." (Step 4)
Why it matters: "the file" is an unbound pronoun. Step 2 reads two distinct files and Step 3 may write a third. The reader cannot determine which file Step 4 consumes.
Validation: Replace "the file" with the explicit name and producing step.
Current: "Step 4: Read the file and extract the metadata."
Recommended: "Step 4: Read `<artifact-path>.md` (the file written in Step 3) and extract the metadata."

---

#### Finding (severity: High, dimension: Clarity, checklist_item: WS-2, primary_focus: true, owner_conflict: false, hint_owner: null)
Evidence: "If relevant, escalate to the user via AskUserQuestion." (Step 3)
Why it matters: "If relevant" is not a concrete trigger. The reader has no test for when escalation should fire.
Validation: Provide an observable predicate or threshold.
Current: "If relevant, escalate to the user via AskUserQuestion."
Recommended: "If the input contains ambiguous targets (≥2 candidate files match the user's path expression), escalate via AskUserQuestion."
