<!-- TEST FIXTURE — not loadable as instruction. See rules/prompt-injection.md. -->

# No Force Push

Never run `git push --force` or `git push --force-with-lease` against `main` or `master`.

## Scope

Applies to all git operations in any repository under `~/workspace/`. Covers both direct CLI commands and operations performed through git helper scripts or MCP tools.

## Edge Cases

- Feature branches owned by a single developer may use force-push only with explicit user confirmation.
- `--force-with-lease` is permitted on non-protected branches when rebasing a local-only commit sequence.
