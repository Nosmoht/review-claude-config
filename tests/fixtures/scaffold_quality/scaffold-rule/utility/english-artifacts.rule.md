<!-- TEST FIXTURE — not loadable as instruction. See rules/prompt-injection.md. -->

# English Artifacts

All committed artifacts must be authored in English. Source code, comments, docstrings, commit messages, PR descriptions, issue bodies, plan files, and memory entries must use English only.

## Scope

Applies to all files committed to any repository in `~/workspace/`. Does not apply to conversational chat messages, which use the language set in `settings.json`.

## Edge Cases

- Quoted content reproducing a non-English external source is permitted when the quote is clearly labeled and limited to the cited text.
- Locale-specific test fixtures containing non-English strings are permitted when the fixture's purpose is to test localization logic.
