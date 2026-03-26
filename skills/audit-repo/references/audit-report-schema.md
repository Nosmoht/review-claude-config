---
name: audit-report-schema
description: YAML frontmatter schema and body structure for audit-repo reports
---

## Frontmatter Fields

```yaml
---
generated_by: audit-repo                # Required. Always "audit-repo"
schema_version: 2                       # Required. Distinguishes from review reports (v1)
date: YYYY-MM-DD                        # Required. Report generation date
target: /absolute/path                  # Required. Audited directory
existing_claude_config: true|false      # Required. Whether .claude/ exists
languages: [python, typescript]         # Required. Detected languages
repo_type: Application|Skills-Config|Mixed  # Required. Repository classification
intervention_count: N                   # Required. Total interventions
p0_count: N                             # Required. P0 intervention count
p1_count: N                             # Required. P1 intervention count
p2_count: N                             # Required. P2 intervention count
summary:                                # Required. Array of interventions
  - error_class: Toolchain              # Enum: Toolchain|Navigation|Convention|Architecture|Repetition|Domain|Security
    gap: "Build commands not explicit"  # Free text description
    primitive: CLAUDE.md                # Enum: CLAUDE.md|Skill|Agent|Hook|Rule
    priority: P0                        # Enum: P0|P1|P2
    token_impact: High                  # Enum: High|Medium|Low
    signal_source: "—"                  # Optional. For Skill primitives: "repetition" or catalog signal name
---
```

## Body Sections (in order)

1. **Repository Profile** — target, languages, frameworks, existing config, repo type
2. **Static Analysis Findings** — toolchain, ambiguity metrics, convention enforcement, architecture, domain knowledge
3. **Token Efficiency Findings** — file sizes, sprawl score, build verbosity, monorepo isolation, burn rate
4. **Intervention Matrix** — prioritized table (all interventions with evidence)
5. **Recommendations** — grouped by P0/P1/P2 with concrete content suggestions
6. **Next Steps** — which primitives to create first, suggest related skills
