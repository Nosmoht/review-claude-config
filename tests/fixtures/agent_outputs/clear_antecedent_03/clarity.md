### Perspective
clarity

### Certificate
| Dimension | Grade | Justification |
|-----------|-------|---------------|
| Clarity | A | All workflow steps state inputs, outputs, and dependencies. Conditionals carry concrete tests. |
| Completeness | A | Happy path, edge cases, and stop conditions all covered. |
| Prompt Engineering | A | Role statement is functional. Output contract specifies a literal template. |
| Context Engineering | A | Stable knowledge lives in references/; SKILL.md body stays under 200 lines. |
| Goal Alignment | A | Single intent, scoped tightly to the user's stated need. |
| Safety | A | Read-only tool grant. No high-risk combinations present. |
| Metadata | A | Frontmatter complete, allowed-tools matches body usage, description is action-verb led. |
| Overall | A | No grade-boundary violations; minor surface polish only. |

### Findings

#### Finding (severity: Low, dimension: Metadata, checklist_item: AP-2, primary_focus: false, owner_conflict: true, hint_owner: integration)
Evidence: "argument-hint: <topic>" in frontmatter
Why it matters: argument-hint is a single placeholder; some users would benefit from an example value alongside.
Validation: Adding an example value (`<topic, e.g. "rate limits">`) would improve discoverability without altering the contract.
Current: `argument-hint: <topic>`
Recommended: `argument-hint: <topic, e.g. "rate limits">`

---

#### Finding (severity: Low, dimension: Prompt Engineering, checklist_item: AP-3, primary_focus: false, owner_conflict: true, hint_owner: correctness)
Evidence: Step 4 worked-example shows ideal output but does not annotate which fields are required vs optional.
Why it matters: Field-level annotations would make the example self-documenting for downstream maintainers.
Validation: This is a polish item, not a correctness issue. Output already passes structural checks.
Current: Worked example without [REQUIRED]/[OPTIONAL] annotations.
Recommended: Add inline annotations on each frontmatter field in the worked example.
