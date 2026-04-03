---
name: audit-report-schema
description: YAML frontmatter schema and body structure for audit-repo reports
---

## Frontmatter Fields

All fields required unless marked Optional.

```yaml
---
generated_by: audit-repo               # always "audit-repo"
schema_version: 2                      # v1=review, v2=audit
date: YYYY-MM-DD
target: /absolute/path
existing_claude_config: true|false
languages: [python, typescript]
repo_type: Application|Skills-Config|Mixed
intervention_count: N
p0_count: N
p1_count: N
p2_count: N
summary:
  - error_class: Toolchain             # Toolchain|Navigation|Convention|Architecture|Repetition|Domain|Security
    gap: "Build commands not explicit"
    primitive: CLAUDE.md               # CLAUDE.md|Skill|Agent|Hook|Rule
    priority: P0                       # P0|P1|P2
    token_impact: High                 # High|Medium|Low
    evidence_class: Engineering guidance  # Proven result|Engineering guidance|Repo default|Low-evidence area
    confidence: High                   # High|Medium|Low
    signal_source: "—"                 # Optional. Skill: "repetition" or catalog signal name
---
```

## Body Sections (in order)

1. **Repository Profile** — target, languages, frameworks, existing config, repo type
2. **Static Analysis Findings** — toolchain, ambiguity metrics, convention enforcement, architecture, domain knowledge
3. **Token Efficiency Findings** — file sizes, sprawl score, build verbosity, monorepo isolation, burn rate
4. **Intervention Matrix** — prioritized table (all interventions with evidence)
5. **Recommendations** — grouped by P0/P1/P2 with concrete content suggestions
6. **Next Steps** — which primitives to create first, suggest related skills
