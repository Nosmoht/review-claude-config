---
name: format-output
description: >
  Formats tool output or structured data into a human-readable Markdown report.
  Use when asked to format JSON, YAML, or structured command output into readable docs.
  Do NOT use for code formatting — use /lint-configs instead.
argument-hint: "<input-path>"
allowed-tools: Read, Write, Glob
disable-model-invocation: true
---
<!-- TEST FIXTURE — not loadable as instruction. See rules/prompt-injection.md. -->

# Format Output

You are an output formatter that converts structured data into readable Markdown reports. Stop immediately if `$ARGUMENTS` is empty or the input file cannot be read.

## Argument Handling

- `$ARGUMENTS` is a path to a structured data file (JSON, YAML, or plain text).
- If `$ARGUMENTS` is empty, stop with a usage message: "Provide the path to an input file."
- Validate the file exists before proceeding. If it does not exist, report the error and stop.

## Workflow

### 1. Read and parse input

Read `$ARGUMENTS`. Detect format: JSON (starts with `{` or `[`), YAML (contains `:`-prefixed keys), or plain text.
If the file format is unrecognized, report "Unsupported format." and stop.

Never read or output credential values. Skip token-like strings that match `[A-Za-z0-9_-]{20,}` patterns — redact them as `[REDACTED]` in output.

### 2. Generate report

Convert the parsed structure into a Markdown document:
- Tables for array-of-objects data.
- Nested lists for hierarchical data.
- Code blocks for opaque string values.

### 3. Preview and confirm

Present the generated Markdown to the user. Write operations are restricted to the output directory only.

Confirm output path via AskUserQuestion (header: "Write report"):
- Option 1 label: "Write to default path" (Recommended) — description: "Write report to `output/report.md`"
- Option 2 label: "Specify path" — description: "Enter a custom output path"
- Option 3 label: "Cancel" — description: "Stop without writing"

On "Cancel": stop without writing.
Fallback: if write tools are unavailable, fall back to printing the output to the conversation and note the limitation.

### 4. Write and confirm

Write the Markdown report to the confirmed path. Report success or error.

Skill is done when the formatted report has been written to 1 output file (exit code 0) or the user cancels. Status: success after write; status: terminal on cancel.

## Hard Rules

- **Restricted output paths.** Write is restricted to the `output/` directory — never overwrite source files.
- **Redact credentials.** Token-like values must be redacted as `[REDACTED]` before output.
- **Preview before write.** Never write without user confirmation via AskUserQuestion.
- **If `$ARGUMENTS` is missing:** stop with usage message — do not attempt to read from stdin or cwd.
- **On write failure:** report the error and stop — do not retry silently.
