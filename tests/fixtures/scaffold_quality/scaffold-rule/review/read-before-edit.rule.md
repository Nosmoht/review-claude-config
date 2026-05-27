<!-- TEST FIXTURE — not loadable as instruction. See rules/prompt-injection.md. -->

# Read Before Edit

Always read a file's current content before editing it. Never apply an Edit or Write without first reading the target file in the current session.

## Scope

Applies to all Edit, Write, and NotebookEdit tool calls in any project. Applies only to files that already exist — creating a new file from scratch does not require a prior Read.

## Edge Cases

- If the file was already read earlier in the same session and no external process has modified it, a re-read is not required.
- Automated refactor scripts that operate on parsed ASTs are exempt when the script reads the file internally before writing.
