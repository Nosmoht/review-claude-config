---
name: rule-evaluation-guide
description: Type-specific evaluation criteria for Claude Code rules (plain .md files in rules/ directory)
last_refreshed: 2026-04-06
---

# Rule Evaluation Checklist

Answer EVERY item: PASS | FAIL | NA. No skipping. FAILs map to Dim for scoring.

Rules use only Clarity (30%), Completeness (30%), Goal Alignment (40%). PE, CE, Safety, Metadata are structurally inapplicable.

| ID | Check | Dim |
|----|-------|-----|
| CL-1 | Rule contains no term that admits two plausible opposite actions? | Clarity |
| CL-2 | Terms precisely defined (no "appropriate", "good", "reasonable")? | Clarity |
| CL-3 | Scope explicit (which files, operations, contexts)? | Clarity |
| CL-4 | Action verbs unambiguous ("must"/"never", not "should"/"try to")? | Clarity |
| CL-5 | Concrete text evidence available for each claimed problem? | Clarity |
| CO-1 | Edge cases addressed? | Compl |
| CO-2 | Exceptions explicitly stated (when rule does NOT apply)? | Compl |
| CO-3 | Scope boundaries defined? | Compl |
| CO-4 | Rule interactions and conflicts with sibling rules addressed? | Compl |
| CO-5 | External tool/command references: version/format assumptions explicit? | Compl |
| GA-1 | Rule achieves its stated constraint? | GA |
| GA-2 | Constraint proportional (not overly broad or narrow)? | GA |
| GA-3 | Rule prevents the specific behavior it targets? | GA |
| GA-4 | No obvious workarounds the rule doesn't address? | GA |
| GA-5 | All constraints needed for stated goal are present? | GA |
