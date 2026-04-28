# Calibration Fixtures

Test fixtures used as anchor artifacts in rubric calibration runs (issue #29 and successors).

**Filename convention.** Fixture skill files end with `.SKILL.md` (e.g., `clear_f_03_kitchen_sink.SKILL.md`), not literal `SKILL.md`. This is load-bearing: the literal-`SKILL.md` glob patterns in `skills/audit-repo`, `skills/suggest-skills`, `scripts/validate_token_budgets.py`, and `scripts/validate_schema.py` do NOT match `*.SKILL.md`. Do not rename to `SKILL.md` or move outside `tests/fixtures/` — either change activates the fixture as if it were a real skill.

**Purpose.** Each fixture is engineered to fail a known set of binary-verifiable rubric items. Fixtures provide stable F-anchor data for divergence calculations in calibration runs. They are not iterated on; if anchors need to change, file a separate issue.
