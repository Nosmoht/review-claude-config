# Schema Conventions

## Required keys
$schema (Draft 2020-12), $id (`review-claude-config:<kind>`), title, description.

## additionalProperties policy
- Frontmatter (ref-file, skill, agent, research, domain-cache, hooks-json): `true`
  — frontmatters carry optional extras (model, tools, argument-hint, etc.).
- Strict-data (token-budgets, audit-triggers, convergence-rules, escalation-rules,
  policy_gate, session_check): `false` — closed contract.

## Naming
`<artifact-kind>.schema.json`, kebab-case.

## Field shape
- `minLength: 1` for non-empty string (after-strip >=20 stays in `_frontmatter.py`).
- `pattern` for date-format only; Feb-30 validity stays in `validate_date()`.
- `oneOf` for polymorphic fields (e.g., agent `tools`: string-OR-array).

## Add a new validator
1. Create `<kind>.schema.json`. 2. Append row to VALIDATORS in `validate_schema.py`.
3. Add fixture to `_setup_valid_repo`. 4. Run `make validate`.

## Error contract
`<file-path>: <message>` — json_path included so field name is visible.

## Auto-wire triggers
`_validate_files` auto-invokes based on schema introspection:
- `description` in `required` -> `_validate_description` (>=20 char after-strip).
- `last_refreshed` in `required` -> `validate_date` (Feb-30 validity).

## SAMP-1/2 belongs in code
`agent.schema.json` does NOT include sampling-param regex constraints.
Raw-text inspection is the only correct check.
