---
name: quality-patterns
description: Generation directives for B+ quality rules — translates rule-evaluation-guide dimension criteria into generator actions. Rules use only 3 dimensions (Clarity 30%, Completeness 30%, Goal Alignment 40%).
last_refreshed: 2026-05-27
---

Translates `rule-evaluation-guide.md` dimension criteria into generator directives.
Rules use only 3 dimensions (Clarity 30%, Completeness 30%, Goal Alignment 40%) per
`scoring-rubric.md §Rule-Specific Scoring`. PE, CE, Safety, and Metadata dimensions
are skipped (rules have no tools, no frontmatter, and are directives not prompts).

## No-Frontmatter
Rules have no YAML frontmatter. Do not generate a `---` block at the start of the
file. The H1 title is the first line. See `rule-template.md §Why Rules Have No
Frontmatter` for rationale.

## Clarity Directives (30%)

### CL-Clarity
- **Sequential steps**: number or bullet each action. No freeform prose for
  multi-part instructions.
- **No bare vague predicates**: forbidden phrases: "if needed", "as appropriate",
  "when useful", "as necessary". Each conditional must name an observable trigger.
- **Explicit trigger conditions**: "When this rule applies" section names the
  observable condition (file type, path pattern, command type) — not "use
  judgment".
- **Negation with positive whitelist**: every NEVER/DO NOT/MUST NOT + verb-list is
  followed within 200 chars by a positive whitelist or "ALLOWED:" clause.
- **Pronoun resolution**: pronouns referring to prior items ("it", "them", "that")
  have explicit antecedents in the same or immediately-preceding sentence.
- **Stop/Recovery**: every abort/refuse/bail/halt/timeout names a recovery target
  within 200 chars (fall back, continue to step N, report and stop).

## Completeness Directives (30%)

### CMP-Completeness
- **Edge cases**: include an "## Edge Cases" section (or equivalent sub-section)
  naming at least 2 edge cases: the boundary condition where the rule applies vs
  where it does not, and the case where a literal reading contradicts the intent.
- **Out-of-scope documentation**: name what the rule does NOT cover (prevents
  silent over-application). Pattern: "## Out of scope: this rule does not apply to
  <excluded class>."
- **Failure modes**: for each mandatory step, name the failure mode and consequence.
  Pattern: "If step N is skipped, <consequence>."
- **When NOT section**: include "When this rule does NOT apply" or an equivalent
  guard to prevent false positives on benign patterns.
- **Anti-patterns section**: name ≥2 anti-patterns — concrete failure behaviors a
  reader might otherwise follow.

## Goal Alignment Directives (40%)

### GA-GoalAlignment
- **Mandate maps to goal**: the `## Mandate` section (or equivalent opening
  section) directly enables the rule's stated objective. Each mandate item is
  traceable to a concrete defect class the rule prevents.
- **Evidence/source anchors**: cite the evidence source that motivates each
  mandatory behavior. Acceptable forms: `arXiv:<id>`, `reference_file.md §Section`,
  `research/<path>.md`. Unsourced mandates are weaker under goal-alignment scoring.
- **Domain-expert checkpoints**: include ≥1 domain-expert checkpoint that is
  explicitly named (not implicit). Omitting a domain-expert step would be detectable
  by a reviewer without running the rule.
- **Anti-gaming**: mandate language is evidence-grounded, not open to trivial
  satisfaction without evidence. "Cite at least one Tier-1 source" is better than
  "cite a source."
- **Premise verification**: when the rule acts on a verifiable premise (file type,
  path predicate, version range), include a verification predicate within 200 chars
  of the premise.

## Structural Directives (enforce via validate_rule_fixture())

### No-Frontmatter
First line of generated rule file must be `# <Title>`, not `---`.

### Required H2 Sections
Generated rules must include all H2 sections present in the canonical structure of
`rule-template.md`. At minimum: `## Scope` and `## Edge Cases`.

### Dimensional Anchor
Body must contain at least one strong enforcement verb (MUST, SHALL, REQUIRED,
PROHIBITED) or a dimension-relevant phrase (Clarity, Completeness, Goal Alignment)
to anchor the rule to its evaluable dimension.

### Body-Length Budget
Keep rule body concise. Use `references/` files for supporting evidence rather than
inlining large tables or long rationale. Budget guideline: reference
`rule-evaluation-guide.md` for the current token budget.
