---
name: quality-patterns
description: Research-backed generation directives for B+ quality skills — translates engineering-baseline evaluator checks into generator actions
last_refreshed: 2026-04-09
---

Translates `engineering-baseline.md` from evaluator checks into generator directives. Load baseline for full citations.

### Activation
Description in user-task terms. Include ≥1 trigger phrase + ≥1 counter-case. Format: `<Verb> <output>. Use when <trigger>. Do NOT use for <exclusion>.`

### Role
`"You are a [role] that [purpose]."` No demographic/expert personas — 26.2% degradation risk. Role adds behavioral context, not credential-stacking.

### Instruction Language
Natural phrasing only. No MUST/CRITICAL/ALWAYS (overtrigger on Claude 4.6). Branch conditions: observable tests, not "if needed".

### Constraints
5–7 hard rules max. Each unconditional — unconditional rules 3.5× more effective. Required: **1 stop condition** + **1 failure path**.

### Context Layout
- START: role + stop conditions
- END: hard rules
- Middle: workflow — different content at each anchor, never repeat

### Output Contract
Verdict/summary first, detail second. State output shape in role or workflow preamble.

### Safety Minimums
Write-capable: stop condition + failure path + confirmation gate + least-privilege tools. Tier A combos (Bash+Write, Bash+network, Write+WebFetch) need inline justification.

### Domain Knowledge
If domain known: inject 2–3 domain-specific rules into workflow or hard rules. Improves quality 30–206%.

### Examples
3–5 `<example>` blocks when trigger or output is ambiguous. More than 5 degrades performance.

### Compaction
Expected turns > 10: add compaction step — testable done criteria defined before execution.
