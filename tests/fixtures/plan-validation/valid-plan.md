# Sample plan with all real references

## Goal

Demonstrate every cited path resolves and every anchor matches an actual
heading in the co-cited markdown file.

## Plan

Read the conventions in `CLAUDE.md` §"Hard Constraints" before editing
configuration. The token-budget enforcement entry point lives in
`scripts/validate_token_budgets.py` and the budget map is at
`skills/review-claude-config/references/token-budgets.json`.

The Makefile entry `Makefile` is the canonical CI surface — see
`CLAUDE.md` §"Architecture" for component naming.

## Fenced block (should be ignored)

```
This block contains `fake/path/that-does-not-exist.py` and §"Nonexistent
Header" — neither should be picked up because they live inside a fenced
code block.
```

## Out of scope

- Editing the rubric or baseline.
