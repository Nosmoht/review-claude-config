---
name: rule-template
description: Canonical structure for Claude Code rule files. Plain Markdown, no frontmatter. Keep under 500 tokens.
last_refreshed: 2026-04-04
---

## Location Convention

Rules live at `.claude/rules/<rule-name>.md` — one file per rule, kebab-case filename.

## Why Rules Have No Frontmatter

Skills and agents use YAML frontmatter to declare tools, invocation control, and trigger metadata. Rules have none of these: they are always-active constraints applied passively to every conversation. No tool access, no invocation control, no model selection — just directive text.

## Canonical Rule Structure

```markdown
# <Rule Name>

<Directive: one or two sentences. Use strong enforcement verbs.>

## Scope

<Which files, tools, commands, or situations this rule applies to.>

## Edge Cases

- <Exception or boundary condition>
- <"None" if truly universal>
```

## Strong Enforcement Verbs

Use these to make rules unambiguous:

- `always` — unconditional requirement
- `never` — unconditional prohibition
- `before X, do Y` — sequencing constraint
- `only when` — conditional allowance
- `stop if` — explicit halt condition

Avoid weak phrasing like "try to", "prefer", or "consider" in rule directives.

## Quality Dimensions

Rules are evaluated on three dimensions only:

| Dimension | Weight | What it checks |
|---|---|---|
| Clarity | 30% | Unambiguous directive language |
| Completeness | 30% | Scope and edge cases defined |
| Goal Alignment | 40% | Rule achieves its stated constraint |

Prompt Engineering, Context Engineering, Safety, and Metadata do not apply — rules have no tools or frontmatter.

## Quality-Gate Mapping

Each section of the canonical structure exists to satisfy specific item IDs
from `skills/review-rule/references/rule-evaluation-guide.md`:

| Template section | Item IDs |
|---|---|
| Directive | CL-1, CL-4, GA-1, GA-3 |
| `## Scope` | CL-3, CO-3 |
| `## Edge Cases` | CO-1, CO-2, GA-4 |
| Thresholds (if any) | EP-1, EP-2 |

Following this template literally hits ≥4 distinct IDs — enough to pass
`/review-rule` without follow-up.

## Verbs that fail CL-4 (do not generate)

Reject: `should`, `try to`, `prefer`, `consider`, `attempt`, `where possible`.
Use instead: `must`, `never`, `always`, `before X do Y`, `only when`, `stop if`.

## Minimal Example

```markdown
# No Force Push

Never run `git push --force` or `git push --force-with-lease` against main or master.

## Scope

Applies to all git operations in any repository. Covers both direct CLI commands and
operations performed through git helper scripts.

## Edge Cases

- Feature branches owned by a single developer may use force-push with explicit user confirmation.
- `--force-with-lease` is permitted on non-protected branches when rebasing is required.
```

## Escalation Policy Example

```markdown
# Escalation Policy

Always escalate when: (1) irreversible operation, (2) confidence <70%,
(3) >3 consecutive tool failures, or (4) credentials/PII access.

## Scope

Workflows using Write, Bash, or Edit. Read-only exempt.

## Edge Cases

- User pre-authorization overrides condition 1 for its scope.
```

## Constraint Load Warning

Adding rules increases cognitive load on the model. If a project already has 5 or more rules covering similar themes (e.g., multiple "no destructive operations" constraints), consolidate into one focused rule rather than adding another. Overlapping rules degrade instruction-following reliability.
