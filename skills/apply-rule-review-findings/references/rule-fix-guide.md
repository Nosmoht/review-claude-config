---
name: rule-fix-guide
description: Type-specific validation rules for applying fixes to Claude Code rules
---

# Rule Fix Guide

## No Frontmatter

Rules are plain Markdown files with no standardized frontmatter. If an edit adds `---` delimiters at the top of the file, strip them. Rules must not have YAML metadata blocks.

## Three Dimensions Only

Rule fixes target only three dimensions:
- **Clarity**: Terms are precisely defined, scope is explicit, no ambiguity
- **Completeness**: Edge cases addressed, scope boundaries defined, exceptions listed
- **Goal Alignment**: Rule achieves its stated constraint proportionally

Do not evaluate or fix against Prompt Engineering, Context Engineering, Safety, or Metadata -- these do not apply to rules.

## Action Verbs

Every directive in a rule must use unambiguous verbs:
- Use: "must", "never", "always", "do not"
- Avoid: "should", "try to", "when possible", "consider", "might want to"

If an edit introduces weak verbs, flag before applying.

## Scope Explicitness

Every rule must specify what it applies to:
- Which files (patterns, directories, extensions)
- Which operations (reads, writes, commits, deploys)
- Which contexts (CI, local dev, production)

If an edit removes scope qualifiers, warn before applying.

## Conflict Detection

After applying edits, read sibling rules in the same directory. Flag contradictions: e.g., one rule says "always use X" while another says "never use X" for overlapping scope.

## Common Pitfalls

- Don't broaden scope beyond the rule's intended constraint
- Don't remove intentional exceptions or edge case handling
- Don't accidentally add frontmatter when the recommendation includes YAML
- Don't weaken enforcement by replacing "must" with "should"
