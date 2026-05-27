---
name: rubric-coverage
description: Maps each rule-rubric quality dimension and structural item to a scaffold-rule generator directive. Binary evaluator is NOT applicable to rules. Source of truth for check_scaffold_quality.py --verify-matrix-complete.
last_refreshed: 2026-05-27
---

# Rubric Coverage Matrix — scaffold-rule

Rules are evaluated under a 3-dimension rubric (Clarity 30%, Completeness 30%, Goal Alignment 40%) per `scoring-rubric.md §Rule-Specific Scoring`. The binary evaluator from `scripts/rubric_binary_evaluator.py` is **NOT applicable** to rules (rules have no frontmatter, no tool grants, and are directives not prompts). Structural validation is performed by `check_scaffold_quality.py` via `validate_rule_fixture()`.

**Coverage scope**: rule dimension directives + structural items (H2 section presence, no-frontmatter assertion, dimensional anchor presence).

`Enforcement` closed set: `by-template | by-AskUserQuestion | by-directive | runtime-OOS`

- `by-template` — scaffold's `rule-template.md` file embeds the requirement at a named slot.
- `by-AskUserQuestion` — scaffold's SKILL.md step 3 collects the value via user-facing prompt.
- `by-directive` — scaffold's `quality-patterns.md` contains an explicit generation directive.
- `runtime-OOS` — runtime-resolved-by-user; NOT scaffold-enforceable. Rationale text mandatory.

## Rule Dimension Directives

| Quality Dimension | Weight | Generator directive (file:section) | Enforcement | Status |
|---|---|---|---|---|
| Clarity (30%) | 0.30 | `quality-patterns.md §CL-Clarity` — directives: sequential step ordering, no bare vague predicates ("if needed", "as appropriate"), explicit trigger conditions, positive-whitelist adjacent to negation blocks | by-directive | in-scope |
| Completeness (30%) | 0.30 | `quality-patterns.md §CMP-Completeness` — directives: edge cases documented, failure modes named, out-of-scope documented in "Out of scope" section, "When this rule applies" / "When this rule does NOT apply" distinction where relevant | by-directive | in-scope |
| Goal Alignment (40%) | 0.40 | `quality-patterns.md §GA-GoalAlignment` — directives: mandate section directly enables the stated goal, anti-patterns section names concrete failure modes, rule includes an evidence/source anchor, workflow includes domain-expert checkpoints | by-directive | in-scope |

## Structural Items (checked by validate_rule_fixture())

| Structural Item | Validator predicate | Generator directive (file:section) | Enforcement | Status |
|---|---|---|---|---|
| No YAML frontmatter | First line is not `---` | `rule-template.md §Why Rules Have No Frontmatter` — template has no frontmatter block; `quality-patterns.md §No-Frontmatter` directive forbids adding frontmatter | by-template | in-scope |
| H1 present and first | First non-empty line is `# <Title>` | `rule-template.md §Canonical Rule Structure` — template slot `# <Rule Title>` is first | by-template | in-scope |
| Required H2 sections present | Sections derived from `rule-template.md §Canonical Rule Structure` at runtime | `rule-template.md §Canonical Rule Structure` — canonical `## Scope` and `## Edge Cases` headings required | by-template | in-scope |
| Dimensional anchor present | Body contains `/\b(Clarity|Completeness|Goal\s+Alignment)\b/i` OR strong enforcement verb | `quality-patterns.md §Dimensional Anchor` — directive instructs LLM to include at least one dimension-relevant verb anchor (MUST/SHALL/REQUIRED/PROHIBITED) | by-directive | in-scope |
| Body length within budget | Character count within `rule-evaluation-guide.md` budget | `quality-patterns.md §Body-Length Budget` — directive: keep rule body concise; reference `references/` files for supporting evidence rather than inlining it | by-directive | in-scope |

## Binary Evaluator Inapplicability Note

The following binary items from `scoring-rubric.md §Binary-Evaluated Items (skill rubric, 30)` are **NOT applicable to rules**:

- META-* items: rules have no frontmatter, therefore no description/tool-list fields to evaluate.
- SAMP-1/SAMP-2: rules have no temperature/sampling parameters.
- CLAR-2, CLAR-3, CLAR-4, WS-2b, WS-5b, WS-6, RD-5b: binary regex checks designed for skill/agent body patterns; rule bodies follow a different structure.
- CE-X: rules have no compaction strategy (rules are not workflow files).
- COMP-V, COMP-W, COMP-X, COMP-Y, COMP-Z, AH-2b: verification criteria designed for skill/agent step workflows.
- SF-3: agent-only metadata item.
- SP-2b, SP-4b, IJ-1b, RL-1b, RL-3b, RL-4b, RL-9b: tool-grant and agentic-reliability items; rules have no tools.

Structural equivalents are enforced by `validate_rule_fixture()` in `check_scaffold_quality.py`.
